import argparse
import json
import requests
import slack_sdk

# Parses and returns the user inputs.
def parse_input():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="./config.json", help="Path to the configuration file.", type=str)
    parser.add_argument("--slack", help="Print result to Slack.", action="store_true")
    return parser.parse_args()

# Loads and returns the configuration file.
def load_config(args):
     with open(args.config, "r") as file:
        return json.load(file)

# Runs checks on the configuration file.
def run_checks(args, config):
    if args.slack and not (config["slack"]["token"] or config["slack"]["channel"]):
        raise ValueError("Propy is supposed to write to Slack, but you did not set the respective `token` or `channel` in the configuration file.")

    if len(config["chains"]) == 0:
        raise ValueError("Propy is supposed to query blockchains, but you did not provide any in the configuration file.")

    for i, chain in enumerate(config["chains"]):
        if not (chain["name"] and chain["address"] and chain["endpoint"]):
            raise ValueError("Propy is supposed to query chains, but you provided an invalid configuration at index %d" % i)

if __name__ == "__main__":
    args = parse_input()
    config = load_config(args)
    run_checks(args, config)

    # Store array of messages to send.
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

    if args.slack:
        # Initialize slack client.
        slack = slack_sdk.WebClient(token=config["slack"]["token"])
        
        # Send to Slack.
        if len(results) > 0:
            for result in results:
                slack.chat_postMessage(channel=config["slack"]["channel"], text=result)
        else: 
            slack.chat_postMessage(channel=config["slack"]["channel"], text="No pending votes!")
    
    for result in results:
        print(result)