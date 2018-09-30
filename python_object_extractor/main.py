import argparse
import sys

from pathlib import Path

from .extractor import extract


def load_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Extract Python object with its dependencies from local project."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        'object_reference',
        type=str,
        help=(
            "reference to object to extract. "
            "Example: 'importable.module:object'"
        ),
    )
    parser.add_argument(
        '-p', '--project_path',
        dest='project_path',
        type=Path,
        default='.',
        help="path to local project directory",
    )
    parser.add_argument(
        '-m', '--output_module_path',
        dest='output_module_path',
        type=Path,
        default='main.py',
        help="path to output Python module containing extracted object",
    )
    parser.add_argument(
        '-r', '--output_requirements_path',
        dest='output_requirements_path',
        type=Path,
        default='requirements.txt',
        help="path to output requirements file",
    )
    return parser.parse_args()


def main() -> None:
    args = load_args()
    project_path = str(args.project_path.absolute())

    if project_path not in sys.path:
        sys.path.insert(0, project_path)

    extract(
        project_path=project_path,
        object_reference=args.object_reference,
        output_module_path=str(args.output_module_path.absolute()),
        output_requirements_path=str(args.output_requirements_path.absolute()),
    )


if __name__ == '__main__':
    main()
