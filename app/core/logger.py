"""
Logging Configuration
Centralized logging for the RAG Summarizer application
"""

import logging
import sys
from datetime import datetime


# ==================== COLORS FOR TERMINAL ====================

class Colors:
    """ANSI color codes for terminal output"""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    
    # Colors
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    GRAY = "\033[90m"


# ==================== CUSTOM FORMATTER ====================

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors and emojis"""
    
    LEVEL_COLORS = {
        logging.DEBUG: Colors.GRAY,
        logging.INFO: Colors.CYAN,
        logging.WARNING: Colors.YELLOW,
        logging.ERROR: Colors.RED,
        logging.CRITICAL: Colors.RED + Colors.BOLD,
    }
    
    LEVEL_EMOJIS = {
        logging.DEBUG: "🔍",
        logging.INFO: "ℹ️ ",
        logging.WARNING: "⚠️ ",
        logging.ERROR: "❌",
        logging.CRITICAL: "🚨",
    }
    
    def format(self, record):
        # Add color and emoji
        color = self.LEVEL_COLORS.get(record.levelno, Colors.WHITE)
        emoji = self.LEVEL_EMOJIS.get(record.levelno, "")
        
        # Format timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Format message
        message = f"{Colors.GRAY}{timestamp}{Colors.RESET} {emoji} {color}{record.getMessage()}{Colors.RESET}"
        
        return message


# ==================== LOGGER SETUP ====================

def setup_logger(name: str = "rag", level: int = logging.INFO) -> logging.Logger:
    """
    Setup and return a configured logger
    
    Args:
        name: Logger name
        level: Logging level
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(ColoredFormatter())
    
    logger.addHandler(console_handler)
    
    return logger


# ==================== GLOBAL LOGGER ====================

logger = setup_logger("rag")


# ==================== CONVENIENCE FUNCTIONS ====================

def log_step(step: str, message: str):
    """Log a step in a process"""
    logger.info(f"{Colors.BOLD}[{step}]{Colors.RESET} {message}")


def log_success(message: str):
    """Log a success message"""
    logger.info(f"{Colors.GREEN}✅ {message}{Colors.RESET}")


def log_error(message: str):
    """Log an error message"""
    logger.error(f"{Colors.RED}❌ {message}{Colors.RESET}")


def log_warning(message: str):
    """Log a warning message"""
    logger.warning(f"{Colors.YELLOW}⚠️  {message}{Colors.RESET}")


def log_debug(message: str):
    """Log a debug message"""
    logger.debug(f"{Colors.GRAY}🔍 {message}{Colors.RESET}")


def log_api(method: str, path: str, status: int = None):
    """Log an API call"""
    status_color = Colors.GREEN if status and status < 400 else Colors.RED
    status_str = f" → {status_color}{status}{Colors.RESET}" if status else ""
    logger.info(f"{Colors.MAGENTA}[API]{Colors.RESET} {method} {path}{status_str}")


def log_db(operation: str, table: str, details: str = ""):
    """Log a database operation"""
    detail_str = f" ({details})" if details else ""
    logger.info(f"{Colors.BLUE}[DB]{Colors.RESET} {operation} on {table}{detail_str}")


def log_llm(action: str, model: str, details: str = ""):
    """Log an LLM operation"""
    detail_str = f" - {details}" if details else ""
    logger.info(f"{Colors.YELLOW}[LLM]{Colors.RESET} {action} with {model}{detail_str}")


def log_embed(action: str, count: int = None):
    """Log an embedding operation"""
    count_str = f" ({count} items)" if count else ""
    logger.info(f"{Colors.CYAN}[EMBED]{Colors.RESET} {action}{count_str}")


def log_chunk(action: str, count: int = None, strategy: str = None):
    """Log a chunking operation"""
    details = []
    if count:
        details.append(f"{count} chunks")
    if strategy:
        details.append(f"strategy: {strategy}")
    detail_str = f" ({', '.join(details)})" if details else ""
    logger.info(f"{Colors.GREEN}[CHUNK]{Colors.RESET} {action}{detail_str}")


def log_search(mode: str, query: str, results: int = None):
    """Log a search operation"""
    query_preview = query[:50] + "..." if len(query) > 50 else query
    result_str = f" → {results} results" if results is not None else ""
    logger.info(f"{Colors.MAGENTA}[SEARCH]{Colors.RESET} {mode}: \"{query_preview}\"{result_str}")
