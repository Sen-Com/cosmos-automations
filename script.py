import requests
import json
import slack_sdk


if __name__ == "__main__":
    # Load configuration.
    with open("config.json", "r") as file:
        config = json.load(file)
    
    # Initialize slack client.
    slack = slack_sdk.WebClient(token=config["slack"]["token"])

    # Store array of messages to send to slack.
    results = []

    # Query open proposals and check votes for every chain.
    for chain in config["chains"]:
        proposals = []
        try:
            proposals = json.loads(requests.get("%s/gov/proposals?status=voting_period" % chain["endpoint"]).text)["result"]
        except Exception as e:
            results.append("Failed to query proposals for %s!" % chain["name"])
        for proposal in proposals:
            vote = ""
            try:
                vote = json.loads(requests.get("%s/gov/proposals/%s/votes/%s" % (chain["endpoint"], proposal["id"], chain["address"])).text)
                if "error" in vote:
                    results.append("Pending vote for proposal #%s on %s!" % (proposal["id"], chain["name"]))
            except Exception as e:
                results.append("Failed to query votes for proposal %s on %s!" % (proposal["id"], chain["name"]))

    # Send to Slack.
    slack.chat_postMessage(
        channel=config["slack"]["channel"],
        text="\n".join(results) if len(results) > 0 else "No pending votes!",
        )