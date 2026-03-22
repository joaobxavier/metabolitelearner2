from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Python port of the MetaboLiteLearner MATLAB workflow.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    convert_parser = subparsers.add_parser("convert-agilent", help="Convert Agilent sample directories into matrix CSVs.")
    convert_parser.add_argument("data_dir")
    convert_parser.add_argument("output_dir")

    extract_parser = subparsers.add_parser("extract-peaks", help="Extract TIC peaks and spectra from matrix CSVs.")
    extract_parser.add_argument("csv_data_dir")
    extract_parser.add_argument("output_spectra_dir")

    workflow_parser = subparsers.add_parser("run-workflow", help="Run the full MetaboLiteLearner workflow.")
    workflow_parser.add_argument("--gcms-csv-dir", default="gcmsCSVs")
    workflow_parser.add_argument("--extracted-peaks-dir", default="extractedPeaks")
    workflow_parser.add_argument("--folds-dir", default="folds")
    workflow_parser.add_argument("--kegg-mat-path", default="kegg/keggCompoundsWithFiehlibSpectrum.mat")
    workflow_parser.add_argument("--regenerate-peaks", action="store_true")
    workflow_parser.add_argument("--kfold-learn", type=int, default=0)
    workflow_parser.add_argument("--max-components", type=int, default=30)
    workflow_parser.add_argument("--nrandomized", type=int, default=1000)
    workflow_parser.add_argument("--shuffle-test", action="store_true")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "convert-agilent":
        from .agilent import convert_agilent_to_csv

        written = convert_agilent_to_csv(args.data_dir, args.output_dir)
        print(f"Wrote {len(written)} matrix CSV files.")
    elif args.command == "extract-peaks":
        from .extract import extract_spectra_and_integrate

        peaks, spectra = extract_spectra_and_integrate(args.csv_data_dir, args.output_spectra_dir)
        print(f"Extracted {len(peaks)} TIC peaks and {len(spectra)} summed spectra.")
    elif args.command == "run-workflow":
        from .workflow import run_workflow

        result = run_workflow(
            gcms_csv_dir=args.gcms_csv_dir,
            extracted_peaks_dir=args.extracted_peaks_dir,
            folds_dir=args.folds_dir,
            kegg_mat_path=args.kegg_mat_path,
            regenerate_peaks=args.regenerate_peaks,
            kfold_learn=args.kfold_learn,
            max_components=args.max_components,
            nrandomized=args.nrandomized,
            shuffle_test=args.shuffle_test,
        )
        print(
            "Completed workflow with "
            f"{len(result.fold_changes)} fold-change peaks and "
            f"{result.learner.nopt} latent components."
        )


if __name__ == "__main__":
    main()
