"""
This module is the entry point of Argos, a real-time image analysis tool for fraud detection.
"""

import argos.src.utils as utils
import argos.src.core.services as services

MAP_TO_MODE_CLASS = {
    "acquire": services.acquire.AcquireService,
    "a": services.acquire.AcquireService,
    "preprocess": services.preprocess.PreprocessService,
    "p": services.preprocess.PreprocessService,
}

MAP_TO_MODE_NAMESPACE_CLASS = {
    "acquire": services.acquire.AcquireServiceNamespace,
    "a": services.acquire.AcquireServiceNamespace,
    "preprocess": services.preprocess.PreprocessServiceNamespace,
    "p": services.preprocess.PreprocessServiceNamespace,
}

if __name__ == "__main__":
    try:
        parser = utils.parser.Parser()

        cmd_line_args = parser.get_args()

        print()
        utils.print_header()
        print()

        mode = cmd_line_args.mode

        if cmd_line_args.command in ["run", "r"]:
            if cmd_line_args.yaml:
                args = MAP_TO_MODE_NAMESPACE_CLASS[mode].from_yaml(cmd_line_args.yaml)
            else:
                cmd_line_args = cmd_line_args.__dict__

                del cmd_line_args["mode"]
                del cmd_line_args["command"]
                args = MAP_TO_MODE_NAMESPACE_CLASS[mode](**cmd_line_args)

            # Run the mode

            utils.print_info(f"{MAP_TO_MODE_CLASS[mode].__name__} settings")
            print(args)
            print()

            USER_CONFIRM = utils.get_user_confirmation("Do you wish to start the data acquisition?")
            print()

            if USER_CONFIRM:
                MAP_TO_MODE_CLASS[mode](args).run()

        else:
            MAP_TO_MODE_CLASS[mode].logs(cmd_line_args.logs_dest)

    except Exception as e:  # pylint: disable=broad-except
        utils.print_error(str(e) + "\n")

        utils.print_warning("Terminating program!\n")

        exit(1)

    except KeyboardInterrupt as e:
        print()
        print()

        utils.print_warning("Terminating program!\n")

        exit(1)

    exit(0)
