import logging
import os
from logging.handlers import RotatingFileHandler
from colorama import Fore, Style, init
import traceback

# Αρχικοποίηση της colorama για χρωματισμό στο τερματικό
init(autoreset=True)

# Απόκτηση του path του τρέχοντος αρχείου
current_dir = os.path.dirname(os.path.abspath(__file__))

class CustomFormatter(logging.Formatter):
    """Custom formatter για τον τερματικό με χρώματα στα επίπεδα log, μαύρο χρώμα για την ημερομηνία/ώρα, μωβ για το αρχείο, και κίτρινο για το όνομα του νήματος."""

    def format(self, record):
        # Καθορισμός του χρώματος για το επίπεδο του log
        if record.levelno == logging.ERROR:
            levelname_color = f"{Fore.RED}{record.levelname}{Style.RESET_ALL}"
            message_color = f"{Fore.RED}{record.getMessage()}{Style.RESET_ALL}"
        elif record.levelno == logging.WARNING:
            levelname_color = f"{Fore.YELLOW}{record.levelname}{Style.RESET_ALL}"
            message_color = record.getMessage()
        elif record.levelno == logging.INFO:
            levelname_color = f"{Fore.BLUE}{record.levelname}{Style.RESET_ALL}"
            message_color = record.getMessage()
        else:
            levelname_color = record.levelname  # Κρατάει το default για άλλα επίπεδα
            message_color = record.getMessage()

        # Προσθήκη μαύρου χρώματος στην ημερομηνία και ώρα
        date_color = f"{Fore.BLACK}{self.formatTime(record, datefmt='%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}"

        # Προσθήκη μωβ χρώματος στο όνομα του αρχείου
        filename_color = f"{Fore.MAGENTA}{record.filename}{Style.RESET_ALL}"

        # Προσθήκη του ονόματος του νήματος με κίτρινο χρώμα
        thread_name_color = f"{Fore.YELLOW}{record.threadName}{Style.RESET_ALL}"

        # Τελικό format για το log message
        log_fmt = f"{date_color} - {levelname_color} - {filename_color} - {thread_name_color} - {message_color}"

        # Εάν υπάρχει exc_info, προσθήκη του traceback στο μήνυμα
        if record.exc_info:
            exc_text = "".join(traceback.format_exception(*record.exc_info))
            log_fmt = f"{log_fmt}\n{Fore.RED}{exc_text}{Style.RESET_ALL}"

        return log_fmt

class LineBasedRotatingFileHandler(RotatingFileHandler):
    """Custom handler that trims log file to a maximum number of lines."""

    def __init__(self, filename, max_lines, **kwargs):
        super().__init__(filename, **kwargs)
        self.max_lines = max_lines

    def emit(self, record):
        super().emit(record)
        self.trim_log_file()

    def trim_log_file(self):
        """Trims the log file to ensure it has no more than self.max_lines lines."""
        if not os.path.isfile(self.baseFilename):
            return

        with open(self.baseFilename, 'r') as file:
            lines = file.readlines()

        if len(lines) <= self.max_lines:
            return

        with open(self.baseFilename, 'w') as file:
            file.writelines(lines[-self.max_lines:])

def setup_logger(name, log_file, level=logging.INFO, console_output=True, max_log_size=10*1024*1024, max_lines=500, backup_count=1):
    """Function to setup a logger with a specific name, log file, and optional colored console output."""

    # Ελέγχει αν ο φάκελος για τα logs υπάρχει, και αν όχι τον δημιουργεί
    log_dir = os.path.dirname(log_file)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Formatter για το αρχείο log
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s - %(threadName)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    # Δημιουργία handler για το αρχείο log με rotation και γραμμική διαχείριση
    file_handler = LineBasedRotatingFileHandler(log_file, max_lines=max_lines, maxBytes=max_log_size, backupCount=backup_count)
    file_handler.setFormatter(file_formatter)

    # Δημιουργία logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(file_handler)

    # Προαιρετικά: Δημιουργία handler για το τερματικό με χρώματα
    if console_output:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(CustomFormatter())
        logger.addHandler(stream_handler)

    return logger

# Δημιουργία των loggers: error_logger, performance_logger, και status_logger
error_logger = setup_logger('error_logger', os.path.join(current_dir, 'logs', 'error.log'), level=logging.WARNING)
performance_logger = setup_logger('performance_logger', os.path.join(current_dir, 'logs', 'performance.log'), console_output=False)
status_logger = setup_logger('status_logger', os.path.join(current_dir, 'logs', 'status.log'))
