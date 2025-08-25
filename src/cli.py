#!/usr/bin/env python3
"""
GUIDE CLI - Unified command-line interface for the GUIDE pipeline.

This module provides a single entry point for all analysis components
with consistent argument handling and configuration management.
"""

import sys
import os
from pathlib import Path
from typing import Optional, List
import typer
from rich.console import Console
from rich.table import Table
from rich import print as rprint

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Now we can import from src
try:
    from src.utils.repro import setup_reproducibility
except ImportError:
    # Fallback for development
    def setup_reproducibility(seed=42):
        import random
        import numpy as np
        random.seed(seed)
        np.random.seed(seed)
        os.environ['PYTHONHASHSEED'] = str(seed)

# Initialize Typer app and console
app = typer.Typer(
    name="guide",
    help="GUIDE: Student Performance Analysis Pipeline",
    add_completion=False,
    rich_markup_mode="rich"
)
console = Console()


def print_banner():
    """Print the GUIDE banner."""
    rprint("""
[bold blue]╔══════════════════════════════════════════════════════════════╗[/bold blue]
[bold blue]║[/bold blue]  [bold green]GUIDE: Student Performance Analysis Pipeline[/bold green]           [bold blue]║[/bold blue]
[bold blue]║[/bold blue]  Publication-grade ML with fairness and explainability    [bold blue]║[/bold blue]
[bold blue]╚══════════════════════════════════════════════════════════════╝[/bold blue]
""")


@app.callback()
def main(
    seed: int = typer.Option(42, "--seed", help="Random seed for reproducibility"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    config_dir: Optional[Path] = typer.Option("configs", "--config-dir", help="Configuration directory")
):
    """GUIDE: Student Performance Analysis Pipeline."""
    if verbose:
        import logging
        logging.basicConfig(level=logging.DEBUG)
    
    # Set up reproducibility
    setup_reproducibility(seed=seed)
    
    # Store global config in a simple way
    if not hasattr(app, 'extra'):
        app.extra = {}
    app.extra['seed'] = seed
    app.extra['verbose'] = verbose
    app.extra['config_dir'] = Path(config_dir)


@app.command()
def train(
    data_path: str = typer.Option("student-mat.csv", "--data", help="Path to dataset"),
    model_type: str = typer.Option("logistic", "--model", help="Model type"),
    config_file: Optional[Path] = typer.Option(None, "--config", help="Training config file"),
    output_dir: Optional[Path] = typer.Option(None, "--output", help="Output directory"),
):
    """Train machine learning models."""
    print_banner()
    console.print("🚀 [bold green]Training Models[/bold green]")
    
    try:
        from src.train import main as train_main
        
        # Import training arguments - we'll need to adapt the existing function
        import argparse
        
        # Create argument namespace to match existing interface
        args = argparse.Namespace()
        args.csv_path = data_path
        args.model_type = model_type
        args.pass_threshold = 10
        args.group_cols = None
        args.param_grid = "default"
        args.estimators = None
        args.final_estimator = "logistic"
        args.base_estimator = "decision_tree"
        args.sequence_model = None
        args.hidden_size = 8
        args.epochs = 50
        args.learning_rate = 0.01
        args.mitigation = "none"
        args.task = "classification"
        
        # Execute training
        console.print(f"📊 Loading data from: {data_path}")
        console.print(f"🤖 Training model: {model_type}")
        
        train_main(**vars(args))
        
        console.print("✅ [bold green]Training completed successfully![/bold green]")
        
    except Exception as e:
        console.print(f"❌ [bold red]Training failed: {e}[/bold red]")
        raise typer.Exit(1)


@app.command()
def fairness(
    data_path: str = typer.Option("student-mat.csv", "--data", help="Path to dataset"),
    sensitive_attr: str = typer.Option("sex", "--sensitive-attr", help="Sensitive attribute"),
    model_path: str = typer.Option("models/model.pkl", "--model", help="Trained model path"),
    config_file: Optional[Path] = typer.Option(None, "--config", help="Fairness config file"),
):
    """Analyze algorithmic fairness and bias."""
    print_banner()
    console.print("⚖️  [bold green]Fairness Analysis[/bold green]")
    
    try:
        from src.train_eval import main as fairness_main
        
        # Create argument namespace
        args = argparse.Namespace()
        args.dataset = Path(data_path)
        args.sensitive_attr = sensitive_attr
        args.model = "logistic"
        args.reports_dir = Path("reports")
        
        console.print(f"📊 Analyzing bias in: {sensitive_attr}")
        console.print(f"🤖 Using model: {model_path}")
        
        fairness_main()
        
        console.print("✅ [bold green]Fairness analysis completed![/bold green]")
        
    except Exception as e:
        console.print(f"❌ [bold red]Fairness analysis failed: {e}[/bold red]")
        raise typer.Exit(1)


@app.command()
def explain(
    model_path: str = typer.Option("models/model.pkl", "--model", help="Trained model path"),
    data_path: str = typer.Option("student-mat.csv", "--data", help="Path to dataset"),
    config_file: Optional[Path] = typer.Option(None, "--config", help="Explainability config file"),
    methods: List[str] = typer.Option(["shap", "lime"], "--methods", help="Explanation methods"),
):
    """Generate model explanations and interpretations."""
    print_banner()
    console.print("🔍 [bold green]Model Explainability[/bold green]")
    
    try:
        from src.explain.importance import main as explain_main
        
        console.print(f"🤖 Explaining model: {model_path}")
        console.print(f"📊 Using data: {data_path}")
        console.print(f"🛠️  Methods: {', '.join(methods)}")
        
        # Execute with simulated args - need to adapt existing function
        import sys
        old_argv = sys.argv
        sys.argv = [
            "importance.py",
            "--model-path", model_path,
            "--data-path", data_path
        ]
        
        explain_main()
        sys.argv = old_argv
        
        console.print("✅ [bold green]Explanation analysis completed![/bold green]")
        
    except Exception as e:
        console.print(f"❌ [bold red]Explanation analysis failed: {e}[/bold red]")
        raise typer.Exit(1)


@app.command()
def early_risk(
    data_path: str = typer.Option("student-mat.csv", "--data", help="Path to dataset"),
    upto_grade: int = typer.Option(1, "--upto-grade", help="Use grades up to G{n}"),
    threshold: float = typer.Option(0.5, "--threshold", help="Risk threshold"),
):
    """Assess early risk of academic failure."""
    print_banner()
    console.print("🚨 [bold green]Early Risk Assessment[/bold green]")
    
    try:
        import subprocess
        import sys
        
        console.print(f"📊 Analyzing risk using grades up to G{upto_grade}")
        console.print(f"⚠️  Risk threshold: {threshold}")
        
        # Execute early risk module
        result = subprocess.run([
            sys.executable, "-m", "src.early_risk",
            "--upto_grade", str(upto_grade)
        ], capture_output=True, text=True, cwd=Path.cwd())
        
        if result.returncode == 0:
            console.print("✅ [bold green]Early risk assessment completed![/bold green]")
            if result.stdout:
                console.print(result.stdout)
        else:
            console.print(f"❌ [bold red]Early risk assessment failed: {result.stderr}[/bold red]")
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"❌ [bold red]Early risk assessment failed: {e}[/bold red]")
        raise typer.Exit(1)


@app.command()
def eda(
    data_path: str = typer.Option("student-mat.csv", "--data", help="Path to dataset"),
    output_dir: Optional[Path] = typer.Option(None, "--output", help="Output directory"),
):
    """Run exploratory data analysis."""
    print_banner()
    console.print("📈 [bold green]Exploratory Data Analysis[/bold green]")
    
    try:
        from src.eda import main as eda_main
        
        console.print(f"📊 Analyzing dataset: {data_path}")
        
        # Execute EDA
        eda_main()
        
        console.print("✅ [bold green]EDA completed successfully![/bold green]")
        console.print("📁 Check the [bold]figures/[/bold] and [bold]tables/[/bold] directories for outputs")
        
    except Exception as e:
        console.print(f"❌ [bold red]EDA failed: {e}[/bold red]")
        raise typer.Exit(1)


@app.command()
def nested_cv(
    data_path: str = typer.Option("student-mat.csv", "--data", help="Path to dataset"),
    outer_folds: int = typer.Option(5, "--outer-folds", help="Outer CV folds"),
    inner_folds: int = typer.Option(3, "--inner-folds", help="Inner CV folds"),
):
    """Run nested cross-validation for model selection."""
    print_banner()
    console.print("🔄 [bold green]Nested Cross-Validation[/bold green]")
    
    try:
        import subprocess
        import sys
        
        console.print(f"📊 Dataset: {data_path}")
        console.print(f"🔄 Outer folds: {outer_folds}, Inner folds: {inner_folds}")
        
        # Execute nested CV module
        result = subprocess.run([
            sys.executable, "-m", "src.nested_cv"
        ], capture_output=True, text=True, cwd=Path.cwd())
        
        if result.returncode == 0:
            console.print("✅ [bold green]Nested CV completed![/bold green]")
            if result.stdout:
                console.print(result.stdout)
        else:
            console.print(f"❌ [bold red]Nested CV failed: {result.stderr}[/bold red]")
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"❌ [bold red]Nested CV failed: {e}[/bold red]")
        raise typer.Exit(1)


@app.command()
def transfer(
    source_dataset: str = typer.Option("student-mat.csv", "--source", help="Source dataset"),
    target_dataset: str = typer.Option("student-por.csv", "--target", help="Target dataset"),
):
    """Run transfer learning experiments."""
    print_banner()
    console.print("🔄 [bold green]Transfer Learning[/bold green]")
    
    try:
        import subprocess
        import sys
        
        console.print(f"📊 Source: {source_dataset}")
        console.print(f"📊 Target: {target_dataset}")
        
        # Execute transfer learning module
        result = subprocess.run([
            sys.executable, "-m", "src.transfer.uci_transfer"
        ], capture_output=True, text=True, cwd=Path.cwd())
        
        if result.returncode == 0:
            console.print("✅ [bold green]Transfer learning completed![/bold green]")
            if result.stdout:
                console.print(result.stdout)
        else:
            console.print(f"❌ [bold red]Transfer learning failed: {result.stderr}[/bold red]")
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"❌ [bold red]Transfer learning failed: {e}[/bold red]")
        raise typer.Exit(1)


@app.command()
def dashboard(
    mode: str = typer.Option("general", "--mode", help="Dashboard mode"),
    port: int = typer.Option(8501, "--port", help="Port number"),
    host: str = typer.Option("localhost", "--host", help="Host address"),
):
    """Launch interactive web dashboard."""
    print_banner()
    console.print("🌐 [bold green]Launching Dashboard[/bold green]")
    
    try:
        import subprocess
        import sys
        
        # Determine dashboard file
        dashboard_files = {
            "general": "dashboard.py",
            "student": "dashboard_student.py", 
            "teacher": "dashboard_teacher.py"
        }
        
        dashboard_file = dashboard_files.get(mode, "dashboard.py")
        
        console.print(f"🚀 Starting {mode} dashboard on {host}:{port}")
        console.print(f"📱 Open http://{host}:{port} in your browser")
        
        # Launch Streamlit
        subprocess.run([
            "streamlit", "run", dashboard_file,
            "--server.port", str(port),
            "--server.address", host
        ])
        
    except KeyboardInterrupt:
        console.print("\n👋 [bold yellow]Dashboard stopped[/bold yellow]")
    except Exception as e:
        console.print(f"❌ [bold red]Dashboard failed: {e}[/bold red]")
        raise typer.Exit(1)


@app.command()
def pipeline(
    data_path: str = typer.Option("student-mat.csv", "--data", help="Path to dataset"),
    steps: List[str] = typer.Option(
        ["eda", "train", "fairness", "explain"], 
        "--steps", 
        help="Pipeline steps to run"
    ),
    output_dir: Path = typer.Option(Path("artifacts"), "--output", help="Output directory"),
):
    """Run complete analysis pipeline."""
    print_banner()
    console.print("🏗️  [bold green]Running Complete Pipeline[/bold green]")
    
    console.print(f"📊 Dataset: {data_path}")
    console.print(f"🔧 Steps: {', '.join(steps)}")
    console.print(f"📁 Output: {output_dir}")
    
    # Create progress table
    table = Table(title="Pipeline Progress")
    table.add_column("Step", style="cyan")
    table.add_column("Status", style="magenta")
    table.add_column("Description", style="white")
    
    for step in steps:
        table.add_row(step, "⏳ Pending", f"Run {step} analysis")
    
    console.print(table)
    
    # Execute steps
    for i, step in enumerate(steps):
        console.print(f"\n🔄 [bold cyan]Step {i+1}/{len(steps)}: {step}[/bold cyan]")
        
        try:
            if step == "eda":
                eda(data_path)
            elif step == "train":
                train(data_path)
            elif step == "fairness":
                fairness(data_path)
            elif step == "explain":
                explain()
            elif step == "early_risk":
                early_risk(data_path)
            elif step == "nested_cv":
                nested_cv(data_path)
            elif step == "transfer":
                transfer()
            else:
                console.print(f"⚠️  [bold yellow]Unknown step: {step}[/bold yellow]")
                continue
                
            console.print(f"✅ [bold green]{step} completed[/bold green]")
            
        except Exception as e:
            console.print(f"❌ [bold red]{step} failed: {e}[/bold red]")
            console.print("🛑 [bold red]Pipeline stopped[/bold red]")
            raise typer.Exit(1)
    
    console.print("\n🎉 [bold green]Pipeline completed successfully![/bold green]")


@app.command()
def status():
    """Show pipeline status and available outputs."""
    print_banner()
    console.print("📊 [bold green]Pipeline Status[/bold green]")
    
    # Check for key files and directories
    status_items = [
        ("Data", "student-mat.csv", "📊"),
        ("Models", "models/", "🤖"),
        ("Figures", "figures/", "📈"),
        ("Tables", "tables/", "📋"),
        ("Reports", "reports/", "📝"),
    ]
    
    table = Table(title="Output Status")
    table.add_column("Component", style="cyan")
    table.add_column("Path", style="white")
    table.add_column("Status", style="magenta")
    table.add_column("Count", style="yellow")
    
    for name, path, icon in status_items:
        path_obj = Path(path)
        if path_obj.exists():
            if path_obj.is_file():
                status = f"✅ {icon} Available"
                count = "1 file"
            else:
                files = list(path_obj.glob("*"))
                status = f"✅ {icon} Available"
                count = f"{len(files)} files"
        else:
            status = f"❌ {icon} Missing"
            count = "0 files"
            
        table.add_row(name, str(path), status, count)
    
    console.print(table)


@app.command()
def config(
    component: str = typer.Argument(help="Component to configure"),
    list_options: bool = typer.Option(False, "--list", help="List configuration options"),
    edit: bool = typer.Option(False, "--edit", help="Edit configuration file"),
):
    """Manage configuration files."""
    print_banner()
    console.print("⚙️  [bold green]Configuration Management[/bold green]")
    
    config_files = {
        "train": "configs/train.yaml",
        "fairness": "configs/fairness.yaml", 
        "explain": "configs/explain.yaml",
        "dashboard": "configs/dashboard.yaml"
    }
    
    if list_options:
        console.print("📋 Available configurations:")
        for comp, file_path in config_files.items():
            exists = "✅" if Path(file_path).exists() else "❌"
            console.print(f"  {exists} {comp}: {file_path}")
        return
    
    if component not in config_files:
        console.print(f"❌ Unknown component: {component}")
        console.print(f"Available: {', '.join(config_files.keys())}")
        raise typer.Exit(1)
    
    config_path = Path(config_files[component])
    
    if not config_path.exists():
        console.print(f"❌ Configuration file not found: {config_path}")
        raise typer.Exit(1)
    
    if edit:
        import os
        editor = os.environ.get('EDITOR', 'nano')
        os.system(f"{editor} {config_path}")
    else:
        console.print(f"📄 Configuration file: {config_path}")
        with open(config_path) as f:
            content = f.read()
        console.print(content)


if __name__ == "__main__":
    app()