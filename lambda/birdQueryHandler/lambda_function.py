import json
import boto3
from decimal import Decimal

TABLE_NAME = "BirdTagsData"
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)
s3 = boto3.client("s3")


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super(DecimalEncoder, self).default(obj)


def parse_get_filters(params):
    filters = {}
    index = 1
    while True:
        tag_key = f"tag{index}"
        count_key = f"count{index}"
        tag = params.get(tag_key)
        count = params.get(count_key)

        if tag is None:
            break

        try:
            count_val = int(count)
            if count_val >= 0:
                filters[tag.lower()] = count_val
        except (TypeError, ValueError):
            filters[tag.lower()] = 1
        index += 1

    return [filters] if filters else []


def parse_post_filters(body_raw):
    try:
        body = json.loads(body_raw)

        if not isinstance(body, list):
            return [], []

        dict_filters = []
        set_filters = []

        for entry in body:
            if isinstance(entry, dict):
                # Old format: { "crow": 2 }
                clean_case = {}
                for k, v in entry.items():
                    if isinstance(k, str) and (isinstance(v, int) and v >= 0):
                        clean_case[k.lower()] = v
                if clean_case:
                    dict_filters.append(clean_case)
            elif isinstance(entry, (list, set)):
                # New format: ["crow", "pigeon"]
                species = [s.lower() for s in entry if isinstance(s, str)]
                if species:
                    set_filters.append(set(species))

        return dict_filters, set_filters

    except Exception:
        return [], []


def lambda_handler(event, context):
    try:
        method = event.get("httpMethod", "").upper()
        if method not in ("GET", "POST"):
            return {
                "statusCode": 405,
                "body": json.dumps({"error": "Method not allowed"})
            }

        # === Extract filters ===
        if method == "GET":
            filters_list = parse_get_filters(event.get("queryStringParameters") or {})
            set_filters = []
        elif method == "POST":
            body_raw = event.get("body", "")
            filters_list, set_filters = parse_post_filters(body_raw)

        if not filters_list and not set_filters:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "No valid filter criteria provided"})
            }

        # === Scan DynamoDB ===
        response = table.scan()
        matching_results = []

        for item in response.get("Items", []):
            birds = item.get("detected_birds", [])
            bird_counts = {}
            for entry in birds:
                if isinstance(entry, dict) and "label" in entry and "count" in entry:
                    label = str(entry["label"]).lower()
                    count = int(entry["count"]) if isinstance(entry["count"], (int, float, Decimal)) else 0
                    bird_counts[label] = count

            # === Dict filter check ===
            matched = False
            for filters in filters_list:
                if method == "GET":
                    if all(bird_counts.get(tag, -1) == filters[tag] for tag in filters):
                        matched = True
                        break
                else:  # POST
                    if all(bird_counts.get(tag, 0) >= filters[tag] for tag in filters):
                        matched = True
                        break

            # === Set filter check ===
            if not matched:
                for required_species in set_filters:
                    if all(bird_counts.get(tag, 0) > 0 for tag in required_species):
                        matched = True
                        break

            if matched:
                result_item = dict(item)  # Clone the item to avoid modifying original

                # Generate presigned URLs for all three S3 fields
                for field in ["annotated_s3_url", "original_s3_url", "thumbnail_s3_url"]:
                    uri = item.get(field)
                    url_field = field.replace("_s3_url", "_url")
                    if uri and uri.startswith("s3://"):
                        try:
                            bucket, key = uri.replace("s3://", "").split("/", 1)
                            presigned = s3.generate_presigned_url(
                                "get_object",
                                Params={"Bucket": bucket, "Key": key},
                                ExpiresIn=300
                            )
                            result_item[url_field] = presigned
                        except Exception as e:
                            print(f"Failed to generate URL for {field}: {e}")
                            result_item[url_field] = None
                    else:
                        result_item[url_field] = None

                matching_results.append(result_item)

        return {
            "statusCode": 200,
            "body": json.dumps({
                "matched_files": matching_results,
                "count": len(matching_results)
            }, cls=DecimalEncoder)
        }

    except Exception as e:
        print("Error:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error", "details": str(e)})
        }
