use clap::{Arg, ArgGroup, Command};
use std::fs;
use std::process::Command as ProcessCommand;

fn main() {
    // Define the command-line arguments using clap
    let matches = Command::new("TeX Expression to PNG")
        .about("Parse command line arguments")
        .long_about(
            r#"
Examples: texExpToPng --exp "E = 5 + m*c^2" --size 800 --output output.png
"#,
        )
        .arg(
            Arg::new("exp")
                .long("exp")
                .help("Input string")
                .value_name("EXPRESSION"),
        )
        .arg(
            Arg::new("file")
                .short('f')
                .long("file")
                .help("The filename containing the expression.")
                .value_name("FILENAME"),
        )
        .group(
            ArgGroup::new("input")
                .required(true)
                .args(&["exp", "file"]),
        )
        .arg(
            Arg::new("size")
                .long("size")
                .help("Image size")
                .required(true)
                .value_name("SIZE"),
        )
        .arg(
            Arg::new("output")
                .long("output")
                .help("Output file")
                .required(true)
                .value_name("OUTPUT_FILE"),
        )
        .get_matches();

    // Get the expression either from command line or a file
    let expression = if let Some(exp) = matches.get_one::<String>("exp") {
        exp.clone()
    } else if let Some(file) = matches.get_one::<String>("file") {
        fs::read_to_string(file).expect("Unable to read file")
    } else {
        panic!("An input expression or file must be provided.");
    };

    let size = matches
        .get_one::<String>("size")
        .expect("Size argument is required")
        .to_string();

    let output = matches
        .get_one::<String>("output")
        .expect("Output argument is required");

    // Write the LaTeX source
    let latex_source = format!(
        r#"
\documentclass{{standalone}}
\usepackage{{amsmath}}
\begin{{document}}
    $ {expression} $
\end{{document}}
"#
    );

    fs::write("formula.tex", latex_source).expect("Unable to write to formula.tex");

    // Run the latex command
    let latex_status = ProcessCommand::new("latex")
        .arg("formula.tex")
        .status()
        .expect("Failed to run latex command");

    if !latex_status.success() {
        eprintln!("LaTeX command failed.");
        return;
    }

    // Run the dvipng command
    let dvipng_status = ProcessCommand::new("dvipng")
        .args(&["-D", &size, "-T", "tight", "-o", output, "formula.dvi"])
        .status()
        .expect("Failed to run dvipng command");

    if !dvipng_status.success() {
        eprintln!("dvipng command failed.");
        return;
    }

    println!("PNG successfully created at {}", output);
}
