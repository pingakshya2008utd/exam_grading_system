import re
import sympy as sp
from sympy.parsing.latex import parse_latex
from typing import Optional, Tuple
from loguru import logger


class MathProcessor:
    """Handle mathematical expression parsing and comparison"""
    
    def parse_expression(self, expr_str: str) -> Optional[sp.Expr]:
        """
        Parse mathematical expression from string
        
        Handles:
        - LaTeX notation: $x^2 + 3x + 2$
        - Standard notation: x**2 + 3*x + 2
        - Fractions: 1/2, \\frac{1}{2}
        
        Args:
            expr_str: Expression string
            
        Returns:
            SymPy expression or None if parsing fails
        """
        if not expr_str:
            return None
        
        try:
            # Remove LaTeX delimiters
            expr_str = expr_str.strip()
            expr_str = expr_str.replace('$', '')
            
            # Try LaTeX parsing first
            if '\\' in expr_str:
                try:
                    return parse_latex(expr_str)
                except:
                    pass
            
            # Replace common LaTeX commands with SymPy equivalents
            expr_str = self._latex_to_sympy(expr_str)
            
            # Try standard SymPy parsing
            return sp.sympify(expr_str)
            
        except Exception as e:
            logger.debug(f"Failed to parse expression '{expr_str}': {e}")
            return None
    
    def _latex_to_sympy(self, latex_str: str) -> str:
        """Convert common LaTeX notation to SymPy format"""
        replacements = {
            r'\\frac\{([^}]+)\}\{([^}]+)\}': r'(\1)/(\2)',
            r'\\sqrt\{([^}]+)\}': r'sqrt(\1)',
            r'\\sin': 'sin',
            r'\\cos': 'cos',
            r'\\tan': 'tan',
            r'\\log': 'log',
            r'\\ln': 'ln',
            r'\\pi': 'pi',
            r'\\infty': 'oo',
            r'\^': '**',
            r'\\times': '*',
            r'\\cdot': '*',
        }
        
        result = latex_str
        for pattern, replacement in replacements.items():
            result = re.sub(pattern, replacement, result)
        
        return result
    
    def extract_numerical_value(self, text: str) -> Optional[float]:
        """
        Extract numerical value from text
        
        Handles:
        - Simple numbers: 42, 3.14
        - Fractions: 1/2, 3/4
        - Scientific notation: 1.5e-3
        - With units: 42 volts, 3.14 meters
        
        Args:
            text: Text containing number
            
        Returns:
            Float value or None
        """
        try:
            # Remove common units and extra text
            text = text.lower().strip()
            text = re.sub(r'[a-z]+$', '', text).strip()
            
            # Try direct float conversion
            try:
                return float(text)
            except:
                pass
            
            # Try fraction
            fraction_match = re.search(r'(-?\d+\.?\d*)\s*/\s*(-?\d+\.?\d*)', text)
            if fraction_match:
                numerator = float(fraction_match.group(1))
                denominator = float(fraction_match.group(2))
                if denominator != 0:
                    return numerator / denominator
            
            # Try scientific notation
            sci_match = re.search(r'(-?\d+\.?\d*)[eE](-?\d+)', text)
            if sci_match:
                return float(text)
            
            # Try extracting any number
            number_match = re.search(r'-?\d+\.?\d*', text)
            if number_match:
                return float(number_match.group())
            
            return None
            
        except Exception as e:
            logger.debug(f"Failed to extract number from '{text}': {e}")
            return None
    
    def compare_expressions(self, expr1_str: str, expr2_str: str,
                          tolerance: float = 0.02) -> Tuple[bool, str]:
        """
        Compare two mathematical expressions for equivalence
        
        Args:
            expr1_str: First expression string
            expr2_str: Second expression string
            tolerance: Numerical tolerance (default 2%)
            
        Returns:
            (is_equivalent, equivalence_type)
            equivalence_type: 'exact', 'numerical', 'partial', 'different'
        """
        # Try symbolic comparison
        expr1 = self.parse_expression(expr1_str)
        expr2 = self.parse_expression(expr2_str)
        
        if expr1 and expr2:
            try:
                # Symbolic equivalence
                if sp.simplify(expr1 - expr2) == 0:
                    return True, 'exact'
                
                # Try numerical evaluation at multiple points
                free_symbols = list(expr1.free_symbols | expr2.free_symbols)
                if free_symbols:
                    # Test at multiple points
                    test_points = [0, 1, -1, 2, 0.5]
                    all_close = True
                    
                    for val in test_points:
                        subs = {sym: val for sym in free_symbols}
                        try:
                            val1 = float(expr1.subs(subs))
                            val2 = float(expr2.subs(subs))
                            
                            if abs(val1 - val2) > max(abs(val1), abs(val2)) * tolerance:
                                all_close = False
                                break
                        except:
                            continue
                    
                    if all_close:
                        return True, 'numerical'
                
            except Exception as e:
                logger.debug(f"Symbolic comparison failed: {e}")
        
        # Try numerical comparison
        num1 = self.extract_numerical_value(expr1_str)
        num2 = self.extract_numerical_value(expr2_str)
        
        if num1 is not None and num2 is not None:
            # Check within tolerance
            if abs(num1 - num2) <= max(abs(num1), abs(num2)) * tolerance:
                return True, 'numerical'
            elif abs(num1 - num2) <= max(abs(num1), abs(num2)) * (tolerance * 2.5):
                # Within 5% tolerance
                return True, 'partial'
        
        return False, 'different'
    
    def format_latex_for_display(self, expr: sp.Expr) -> str:
        """
        Format SymPy expression as LaTeX for display
        
        Args:
            expr: SymPy expression
            
        Returns:
            LaTeX string
        """
        try:
            return sp.latex(expr)
        except:
            return str(expr)
