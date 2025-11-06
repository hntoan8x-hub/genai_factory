# shared_libs/atomic/tools/data_analyzer_tool.py
import pandas as pd
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, validator
from shared_libs.base.base_tool import BaseTool
from shared_libs.exceptions import ToolExecutionError

# --- Pydantic Schemas ---
class AnalysisInput(BaseModel):
    """Schema for the input of the Data Analyzer Tool."""
    data: List[Dict] = Field(..., description="The raw list of dictionaries/JSON data to analyze.")
    analysis_type: str = Field(..., description="The type of analysis to perform (e.g., 'calculate_mean', 'check_outliers', 'describe_stats').")
    target_column: str = Field(..., description="The column name to perform numerical analysis on.")

class AnalysisOutput(BaseModel):
    """Schema for the output of the Data Analyzer Tool."""
    analysis_result: Dict[str, Any] = Field(..., description="The structured result of the statistical analysis.")
    summary: str = Field(..., description="A plain language summary of the findings.")

# --- Tool Implementation ---
class DataAnalyzerTool(BaseTool):
    """
    A tool for performing statistical and numerical analysis on raw data,
    leveraging Pandas for robust processing.
    """

    @property
    def name(self) -> str:
        return "data_analyzer"

    @property
    def description(self) -> str:
        return "Perform statistical analysis (mean, standard deviation, outliers) on tabular data received from other tools."

    @property
    def input_schema(self) -> BaseModel:
        return AnalysisInput
    
    @property
    def output_schema(self) -> BaseModel:
        return AnalysisOutput

    def __init__(self):
        # Không cần kết nối ngoài, chỉ cần thư viện Pandas
        pass

    def _perform_analysis(self, parsed_input: AnalysisInput) -> Dict[str, Any]:
        """Thực hiện phân tích Pandas dựa trên loại yêu cầu."""
        try:
            df = pd.DataFrame(parsed_input.data)
            target = parsed_input.target_column
            
            # Đảm bảo cột mục tiêu là số
            if not pd.api.types.is_numeric_dtype(df[target]):
                 df[target] = pd.to_numeric(df[target], errors='coerce')
                 df.dropna(subset=[target], inplace=True)
            
            if df.empty:
                raise ValueError("Dataset is empty or target column is non-numeric.")

            analysis_type = parsed_input.analysis_type.lower()
            
            if analysis_type == 'calculate_mean':
                result = {'mean': df[target].mean()}
                summary = f"The average ({target}) is {result['mean']:.2f}."
            
            elif analysis_type == 'describe_stats':
                stats = df[target].describe().to_dict()
                result = {k: round(v, 2) for k, v in stats.items()}
                summary = f"Summary statistics for {target}: Mean={result['mean']}, Std={result['std']}, Min={result['min']}, Max={result['max']}."

            elif analysis_type == 'check_outliers':
                Q1 = df[target].quantile(0.25)
                Q3 = df[target].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                outliers = df[(df[target] < lower_bound) | (df[target] > upper_bound)]
                result = {
                    'total_rows': len(df),
                    'outlier_count': len(outliers),
                    'outlier_percent': len(outliers) / len(df) if len(df) > 0 else 0,
                }
                summary = f"Found {result['outlier_count']} outliers in {target}, accounting for {result['outlier_percent'] * 100:.2f}% of the data."
                
            else:
                raise ValueError(f"Analysis type '{parsed_input.analysis_type}' is not supported.")
                
            return AnalysisOutput(analysis_result=result, summary=summary).model_dump()

        except Exception as e:
            raise ToolExecutionError(f"Data analysis failed: {e.__class__.__name__}: {str(e)}")

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous run method."""
        try:
            # ToolService đã thực hiện validation ban đầu, nhưng chúng ta chạy lại để phân tích
            parsed_input = AnalysisInput.model_validate(input_data)
            # Vì Pandas I/O thường là sync và nhanh, ta dùng run()
            return self._perform_analysis(parsed_input)
        except Exception as e:
             raise ToolExecutionError(f"Data analysis setup failed: {e}")

    # Tool này không thực sự cần async vì nó chủ yếu là CPU-bound (Pandas processing)
    async def async_run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Asynchronous wrapper for the synchronous analysis (chạy trong ThreadPoolExecutor nếu cần)."""
        # Để đơn giản, ta gọi sync từ async (giả định thread đã được quản lý ở ToolService)
        return self.run(input_data)