import os

import requests
import json
from .models import CarDealer, DealerReview
from requests.auth import HTTPBasicAuth


# Create a `get_request` to make HTTP GET requests
# e.g., response = requests.get(url, params=params, headers={'Content-Type': 'application/json'},
#                                     auth=HTTPBasicAuth('apikey', api_key))
def get_request(url, **kwargs):
    print(kwargs)
    print("GET from {} ".format(url))
    response = None
    api_key = kwargs.setdefault('api_key', None)
    try:
        # Call get method of requests library with URL and parameters
        if api_key:
            # Basic authentication GET
            requests.get(url, params=kwargs, headers={'Content-Type': 'application/json'},
                         auth=HTTPBasicAuth('apikey', api_key))
        else:
            # no authentication GET
            response = requests.get(
                url, headers={'Content-Type': 'application/json'}, params=kwargs)
    except:
        # If any error occurs
        print("Network exception occurred")
    if response:
        status_code = response.status_code
        print("With status {} ".format(status_code))
        json_data = json.loads(response.text)
        return json_data
    else:
        print("Response not set")
        return ""


# Create a `post_request` to make HTTP POST requests
# e.g., response = requests.post(url, params=kwargs, json=payload)
def post_request(url, **kwargs):
    print(kwargs)
    print("POST to {} ".format(url))
    response = None
    api_key = kwargs.setdefault('api_key', None)
    json_payload = kwargs.setdefault('json_payload', None)
    try:
        # Call get method of requests library with URL and parameters
        if api_key:
            # Basic authentication POST
            requests.post(url, params=kwargs, headers={'Content-Type': 'application/json'},
                          auth=HTTPBasicAuth('apikey', api_key), json=json_payload)
        else:
            # no authentication POST
            response = requests.post(url, headers={
                                     'Content-Type': 'application/json'}, params=kwargs, json=json_payload)
    except:
        # If any error occurs
        print("Network exception occurred")
    if response:
        status_code = response.status_code
        print("With status {} ".format(status_code))
        json_data = json.loads(response.text)
        return json_data
    else:
        print("Response not set")


# Create a get_dealers_from_cf method to get dealers from a cloud function
# def get_dealers_from_cf(url, **kwargs):
# - Call get_request() with specified arguments
# - Parse JSON results into a CarDealer object list
def get_dealers_from_cf(url, **kwargs):
    results = []
    # Call get_request with a URL parameter
    json_result = get_request(url)
    if json_result:
        # Get the row list in JSON as dealers
        dealers = json_result["rows"]
        # For each dealer object
        for dealer in dealers:
            # Get its content in `doc` object
            dealer_doc = dealer["doc"]
            # Create a CarDealer object with values in `doc` object
            dealer_obj = CarDealer(address=dealer_doc["address"], city=dealer_doc["city"], full_name=dealer_doc["full_name"],
                                   id=dealer_doc["id"], lat=dealer_doc["lat"], long=dealer_doc["long"],
                                   short_name=dealer_doc["short_name"],
                                   st=dealer_doc["st"], zip=dealer_doc["zip"])

            results.append(dealer_obj)

    return results


# Create a get_dealer_reviews_from_cf method to get reviews by dealer id from a cloud function
def get_dealer_reviews_from_cf(url, dealer_id):
    results = []
    # Call get_request with a URL parameter
    json_result = get_request(url + '?dealerId=' + str(dealer_id))
    if json_result:
        # Get the row list in JSON as dealers
        reviews = json_result["rows"]
        # For each review object
        for review in reviews:
            # Get its content in `doc` object
            review_doc = review["doc"]
            # Create a DealerReview object with values in `doc` object
            review_obj = DealerReview(dealership=review_doc["dealership"],
                                      name=review_doc["name"],
                                      purchase=review_doc["purchase"],
                                      review=review_doc["review"],
                                      purchase_date=review_doc["purchase_date"],
                                      car_make=review_doc["car_make"],
                                      car_model=review_doc["car_model"],
                                      car_year=review_doc["car_year"],
                                      # sentiment=review_doc["sentiment"],
                                      sentiment=None,
                                      id=review_doc["id"])
            review_obj.sentiment = analyze_review_sentiments(review_obj.review)
            results.append(review_obj)

    return results


# def get_dealer_by_id_from_cf(url, dealerId):
# - Call get_request() with specified arguments
# - Parse JSON results into a DealerView object list
def get_dealer_by_id_from_cf(url, dealer_id):
    results = []
    # Call get_request with a URL parameter
    json_result = get_request(url + '?dealerId=' + str(dealer_id))
    if json_result:
        # Get the row list in JSON as dealers
        dealers = json_result["rows"]
        # For each dealer object
        for dealer in dealers:
            # Get its content in `doc` object
            dealer_doc = dealer["doc"]
            # Create a CarDealer object with values in `doc` object
            dealer_obj = CarDealer(address=dealer_doc["address"], city=dealer_doc["city"], full_name=dealer_doc["full_name"],
                                   id=dealer_doc["id"], lat=dealer_doc["lat"], long=dealer_doc["long"],
                                   short_name=dealer_doc["short_name"],
                                   st=dealer_doc["st"], zip=dealer_doc["zip"])
            results.append(dealer_obj)

    return results


# Create an `analyze_review_sentiments` method to call Watson NLU and analyze text
# def analyze_review_sentiments(text):
# - Call get_request() with specified arguments
# - Get the returned sentiment label such as Positive or Negative
def analyze_review_sentiments(dealerreview):
    # params = dict()
    # params["text"] = kwargs["text"]
    # params["version"] = kwargs["version"]
    # params["features"] = kwargs["features"]
    # params["return_analyzed_text"] = kwargs["return_analyzed_text"]
    # response = requests.get(url, params=params, headers={'Content-Type': 'application/json'},
    #                         auth=HTTPBasicAuth('apikey', api_key))
    # return response

    url = os.getenv('NLP_SENTIMENT_PREDICT_URL')
    myobj = {"raw_document": {"text": dealerreview}}
    header = {
        "grpc-metadata-mm-model-id": "sentiment_aggregated-bert-workflow_lang_multi_stock"}
    response = requests.post(url, json=myobj, headers=header)
    formatted_response = json.loads(response.text)
    label = None
    score = None

    if response.status_code == 200:
        label = formatted_response['documentSentiment']['label']
        score = formatted_response['documentSentiment']['score']
    elif response.status_code == 500:
        label = None
        score = None
    return {'label': label, 'score': score}
