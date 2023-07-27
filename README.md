# Email API Microservice

## Requesting Data (Sending an Email)

The email microservice operates via a POST-only API. The endpoint for this API is https://vmufy6xes4.execute-api.us-east-1.amazonaws.com/default/Lambda_SES_Microservice. The endpoint requires an API key to be accessed otherwise the service will not be able to execute.

The service requires data sent via POST to be in JSON format of the following form:


**{
"title":  string,
"recipients": array of strings (valid email addresses),
"message": string
}**

The order of the keys in the JSON does not matter, but the types are strict. If any of the conditions are failed, the service will return that an internal server error has occurred.

The request can be ran in a CLI. An example call for the service is:

**curl -X POST "https://vmufy6xes4.execute-api.us-east-1.amazonaws.com/default/Lambda_SES_Microservice" \
-H "Content-Type: application/json" \
-H "x-api-key: API-KEY" \
-d @test.json**

Upon satisfaction of the requirements, the service will send an email to the addresses in the recipients array with the specified title and message.

## Receiving Data

The only information that this service sends to the caller is a confirmation notice or a notice of failure. If the service has failed, then the following notice will be seen:

**"Internal Server Error"**

If the service has succeeded, then the following notice will be seen:

**"Message Sent Successfully. {:message_id=>\"MESSAGE_ID"} "**

The processing of these notices are left to the caller.

## UML

Sending Data & Receiving Return Notice
```mermaid

flowchart RL
	subgraph Call Stage
	A[Caller] -- POST Request --> B[API Endpoint]
	end
	subgraph Processing Stage
	B[API Endpoint] --> C[AWS Lambda]
end
	C[AWS Lambda] -- Email Information --> D[Amazon SES] -.-> C[AWS Lambda] -.-> B[API Endpoint] -. Return Notice .-> A[Caller]
	subgraph Recipient Stage
		D[Amazon SES] -- Email --> E[Email Recipient]
	end
