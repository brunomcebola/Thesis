import sys
import argparse


class MyParser(argparse.ArgumentParser):
    def error(self, message):
        print(f"error: {message}")
        if len({"a", "aquire"}.intersection(sys.argv[1:])):
            self.parse_args(["a", "-h"])
        elif len({"t", "train"}.intersection(sys.argv[1:])):
            self.parse_args(["t", "-h"])
        elif len({"o", "online"}.intersection(sys.argv[1:])):
            self.parse_args(["o", "-h"])
        else:
            self.print_help()
        self.exit(2)


def parse_args():
    # Create the argument parser
    parser = MyParser(
        description="Argos, Real-time Image Analysis for Fraud Detection",
        formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=30),
    )

    subparsers = parser.add_subparsers(title="Modes", dest="mode", required=True, metavar="{aquire,train,online}")

    # create the parser for the "aquire" mode
    parser_a = subparsers.add_parser("aquire", aliases="a", help="Mode to capture and store video.", )

    # create the parser for the "train" mode
    parser_t = subparsers.add_parser("train", aliases="t", help="Mode to train a model.")

    # create the parser for the "online" mode
    parser_o = subparsers.add_parser("online", aliases="o", help="Mode to run the model online.")

    args = vars(parser.parse_args())

    return args


if __name__ == "__main__":
    args = parse_args()

    if args["mode"] in ["aquire", "a"]:
        print("aquire")
    elif args["mode"] in ["train", "t"]:
        pass
    elif args["mode"] in ["online", "o"]:
        pass
    else:
        raise Exception("Unknown mode.")
