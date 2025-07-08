import sys
import os
import warnings
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

from requirements_taker_crew.crew import RequirementsTakerCrew

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('requirements_analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Suppress warnings
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")
warnings.filterwarnings("ignore", category=UserWarning, module="crewai")

class RequirementsAnalysisRunner:
    """Main runner class for the requirements analysis system."""
    
    def __init__(self):
        self.current_year = str(datetime.now().year)
        self.required_files = [
            "credentials.json"
        ]
        self.required_env_vars = [
            "OPENAI_API_KEY",
            "GOOGLE_DRIVE_FOLDER_ID"
        ]
    
    def validate_environment(self) -> bool:
        """Validate that all required environment variables and files exist."""
        logger.info("🔍 Validating environment...")
        
        # Check required files
        missing_files = []
        for file_path in self.required_files:
            if not Path(file_path).exists():
                missing_files.append(file_path)
        
        if missing_files:
            logger.error("❌ Missing required files:")
            for file in missing_files:
                logger.error(f"   - {file}")
            logger.error("\nPlease ensure these files exist:")
            logger.error("   - credentials.json: Google OAuth credentials")
            logger.error("   - Use credentials.json.example as template")
            return False
        
        # Check required environment variables
        missing_vars = []
        for var in self.required_env_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.error("❌ Missing required environment variables:")
            for var in missing_vars:
                logger.error(f"   - {var}")
            logger.error("\nPlease set these in your .env file:")
            logger.error("   - OPENAI_API_KEY: Your OpenAI API key")
            logger.error("   - GOOGLE_DRIVE_FOLDER_ID: Target Google Drive folder ID")
            logger.error("   - Use .env.example as template")
            return False
        
        logger.info("✅ Environment validation successful")
        return True
    
    def get_folder_id(self, args: list = None) -> Optional[str]:
        """Get folder ID from command line args or environment."""
        # Command line takes precedence
        if args and len(args) > 1:
            return args[1]
        
        # Fall back to environment variable
        return os.getenv('GOOGLE_DRIVE_FOLDER_ID')
    
    def run_analysis(self, folder_id: Optional[str] = None, args: list = None) -> bool:
        """Run the comprehensive requirements analysis."""
        try:
            # Validate environment
            if not self.validate_environment():
                return False
            
            # Get folder ID
            if not folder_id:
                folder_id = self.get_folder_id(args or sys.argv)
            
            if not folder_id:
                logger.error("❌ ERROR: Google Drive folder ID not provided")
                logger.error("\nYou can provide it by:")
                logger.error("1. Command line: python main.py <folder_id>")
                logger.error("2. Environment variable: GOOGLE_DRIVE_FOLDER_ID=<folder_id>")
                logger.error("3. .env file: GOOGLE_DRIVE_FOLDER_ID=<folder_id>")
                return False
            
            # Prepare inputs
            inputs = {
                'folder_id': folder_id,
                'current_year': self.current_year
            }
            
            # Display startup information
            self._display_startup_info(folder_id)
            
            # Initialize and run crew
            logger.info("🚀 Initializing CrewAI system...")
            crew = RequirementsTakerCrew().crew()
            
            logger.info("📊 Starting comprehensive requirements analysis...")
            result = crew.kickoff(inputs=inputs)
            
            # Success message
            logger.info("\n" + "="*60)
            logger.info("🎉 Requirements analysis completed successfully!")
            logger.info("📄 Detailed report saved to: questionnaire.md")
            logger.info("📄 Final report saved to: final_requirements_analysis_report.md")
            logger.info("📋 Log file saved to: requirements_analysis.log")
            logger.info("="*60)
            
            return True
            
        except KeyboardInterrupt:
            logger.warning("\n⚠️ Analysis interrupted by user")
            return False
        except Exception as e:
            logger.error(f"\n💥 Analysis failed: {str(e)}")
            logger.error("\nTroubleshooting tips:")
            logger.error("1. Verify Google Drive folder ID is correct and accessible")
            logger.error("2. Check credentials.json has valid OAuth credentials")
            logger.error("3. Ensure you have access to the Google Drive folder")
            logger.error("4. Verify all required Python packages are installed")
            logger.error("5. Check internet connectivity")
            raise e
    
    def _display_startup_info(self, folder_id: str):
        """Display startup information."""
        logger.info("\n" + "="*60)
        logger.info("🚀 CREWAI REQUIREMENTS ANALYSIS SYSTEM")
        logger.info("="*60)
        logger.info(f"📁 Target Folder ID: {folder_id}")
        logger.info(f"🔑 Credentials: credentials.json")
        logger.info(f"📅 Analysis Year: {self.current_year}")
        logger.info(f"🤖 Model: {os.getenv('MODEL', 'gpt-4')}")
        logger.info("="*60)


def run():
    """
    Main entry point function expected by CrewAI.
    This function is called by the run_crew script.
    """
    try:
        logger.info("🎯 Starting CrewAI Requirements Analysis")
        runner = RequirementsAnalysisRunner()
        success = runner.run_analysis()
        
        if success:
            logger.info("✅ Analysis completed successfully")
            return "Analysis completed successfully"
        else:
            logger.error("❌ Analysis failed")
            return "Analysis failed"
            
    except Exception as e:
        logger.error(f"💥 Unexpected error: {str(e)}")
        raise e


def train():
    """Train the crew for improved performance."""
    try:
        if len(sys.argv) < 4:
            logger.error("Usage: python main.py train <folder_id> <iterations> <filename>")
            return False
        
        folder_id = sys.argv[2]
        n_iterations = int(sys.argv[3])
        filename = sys.argv[4]
        
        inputs = {
            "folder_id": folder_id,
            'current_year': str(datetime.now().year)
        }
        
        logger.info(f"🎯 Training crew with {n_iterations} iterations...")
        RequirementsTakerCrew().crew().train(
            n_iterations=n_iterations, 
            filename=filename, 
            inputs=inputs
        )
        logger.info("✅ Training completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"💥 Training failed: {str(e)}")
        return False


def replay():
    """Replay a specific task execution."""
    try:
        if len(sys.argv) < 3:
            logger.error("Usage: python main.py replay <task_id>")
            return False
        
        task_id = sys.argv[2]
        logger.info(f"🔄 Replaying task: {task_id}")
        RequirementsTakerCrew().crew().replay(task_id=task_id)
        logger.info("✅ Replay completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"💥 Replay failed: {str(e)}")
        return False


def test():
    """Test the crew with evaluation metrics."""
    try:
        if len(sys.argv) < 5:
            logger.error("Usage: python main.py test <folder_id> <iterations> <eval_llm>")
            return False
        
        folder_id = sys.argv[2]
        n_iterations = int(sys.argv[3])
        eval_llm = sys.argv[4]
        
        inputs = {
            "folder_id": folder_id,
            "current_year": str(datetime.now().year)
        }
        
        logger.info(f"🧪 Testing crew with {n_iterations} iterations...")
        RequirementsTakerCrew().crew().test(
            n_iterations=n_iterations, 
            eval_llm=eval_llm, 
            inputs=inputs
        )
        logger.info("✅ Testing completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"💥 Testing failed: {str(e)}")
        return False


def display_help():
    """Display help information."""
    print("\n🔧 CrewAI Requirements Analysis System")
    print("="*50)
    print("Usage:")
    print("  python main.py [folder_id]                    # Run analysis")
    print("  python main.py train <folder_id> <iter> <file> # Train crew")
    print("  python main.py replay <task_id>                # Replay task")
    print("  python main.py test <folder_id> <iter> <llm>   # Test crew")
    print("  python main.py help                            # Show this help")
    print("\nExamples:")
    print("  python main.py 1ABC23def4GHI56jkl7MNO89pqr")
    print("  python main.py train 1ABC23def4GHI56jkl7MNO89pqr 5 training_data.json")
    print("\nEnvironment:")
    print("  GOOGLE_DRIVE_FOLDER_ID - Default folder ID")
    print("  OPENAI_API_KEY - Required for AI processing")
    print()


def main():
    """Main entry point when called directly."""
    # Handle command line arguments
    if len(sys.argv) >= 2:
        command = sys.argv[1].lower()
        
        if command in ["help", "-h", "--help"]:
            display_help()
            return
        elif command == "train":
            success = train()
        elif command == "replay":
            success = replay()
        elif command == "test":
            success = test()
        else:
            # Treat as folder_id and run analysis
            runner = RequirementsAnalysisRunner()
            success = runner.run_analysis()
    else:
        # No arguments provided, run with environment variable
        success = run()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()