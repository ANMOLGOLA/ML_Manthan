import re
from datetime import datetime
from typing import Optional, Any

class Normalizer:
    @staticmethod
    def parse_currency(value: Any) -> float:
        if value is None:
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        
        # Clean string currency formats: e.g. "$ 5,500.00", "₹ 75,000", "75k", "USD 10000"
        str_val = str(value).strip().lower()
        if not str_val:
            return 0.0
            
        # Check for 'k' / 'M' multiplier
        multiplier = 1.0
        if str_val.endswith('k'):
            multiplier = 1000.0
            str_val = str_val[:-1]
        elif str_val.endswith('m'):
            multiplier = 1000000.0
            str_val = str_val[:-1]
            
        # Extract digits, minus, and decimal point
        cleaned = re.sub(r'[^\d.-]', '', str_val)
        try:
            return float(cleaned) * multiplier if cleaned else 0.0
        except ValueError:
            return 0.0

    @staticmethod
    def parse_date(date_str: Optional[str]) -> Optional[str]:
        if not date_str:
            return None
        date_str = date_str.strip()
        
        formats = [
            "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y",
            "%d %b %Y", "%d %B %Y", "%Y/%m/%d"
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
                
        # Regex fallback for YYYY-MM-DD or DD-MM-YYYY
        match = re.search(r'(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})', date_str)
        if match:
            return f"{match.group(1)}-{int(match.group(2)):02d}-{int(match.group(3)):02d}"
            
        match_reverse = re.search(r'(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})', date_str)
        if match_reverse:
            return f"{match_reverse.group(3)}-{int(match_reverse.group(2)):02d}-{int(match_reverse.group(1)):02d}"
            
        return date_str
