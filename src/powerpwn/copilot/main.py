from powerpwn.cli.arguments import parse_arguments
from powerpwn.copilot.enums.copilot_scenario_enum import CopilotScenarioEnum
from powerpwn.copilot.enums.verbose_enum import VerboseEnum
from powerpwn.copilot.interactive_chat.interactive_chat import InteractiveChat
from powerpwn.copilot.models.chat_argument import ChatArguments


def main():
    print("Copilot for Microsoft 365 - command line edition")
    args = parse_arguments()

    parsed_args = ChatArguments(
        user=args.user,
        password=args.password,
        verbose=VerboseEnum(args.verbose),
        scenario=CopilotScenarioEnum(args.scenario),
    )

    InteractiveChat(parsed_args).start_chat()


if __name__ == "__main__":
    main()
