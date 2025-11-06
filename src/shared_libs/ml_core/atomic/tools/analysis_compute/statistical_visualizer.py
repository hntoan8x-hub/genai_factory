# shared_libs/atomic/tools/analysis_compute/statistical_visualizer.py
import pandas as pd
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from shared_libs.base.base_tool import BaseTool
from shared_libs.exceptions import ToolExecutionError

class VisualizerInput(BaseModel):
    """Schema for the input of the Statistical Visualizer Tool."""
    data: List[Dict] = Field(..., description="The raw list of dictionaries/JSON data to visualize.")
    chart_type: str = Field(..., description="The type of chart required (e.g., 'bar', 'line', 'scatter', 'histogram').")
    x_axis: str = Field(..., description="The column name for the X-axis (or numerical data).")
    y_axis: Optional[str] = Field(None, description="The column name for the Y-axis (required for bar/line/scatter).")
    title: str = Field("Generated Chart", description="Title for the chart.")

class VisualizerOutput(BaseModel):
    """Schema for the output of the Statistical Visualizer Tool."""
    python_code: str = Field(..., description="The generated Python code snippet for the visualization (e.g., Plotly code).")
    success: bool = Field(..., description="Indicates if the code was successfully generated.")

class StatisticalVisualizer(BaseTool):
    """
    A tool that generates Python code for statistical visualization (e.g., Plotly)
    from structured data. The code can be executed in a safe sandbox by the Agent.
    """

    @property
    def name(self) -> str:
        return "statistical_visualizer"

    @property
    def description(self) -> str:
        return "Generates a complete, ready-to-run Python code snippet (using libraries like Plotly or Matplotlib) to visualize tabular data."

    @property
    def input_schema(self) -> BaseModel:
        return VisualizerInput
    
    @property
    def output_schema(self) -> BaseModel:
        return VisualizerOutput

    def _generate_plotly_code(self, df: pd.DataFrame, input: VisualizerInput) -> str:
        """Tạo mã Plotly dựa trên input."""
        df_json = df.to_json(orient='records')
        
        # Tạo mã Plotly/Pandas đơn giản
        code = f"""
import pandas as pd
import plotly.express as px
import json

# Load data from the context (or internal file)
data = json.loads('{df_json}')
df = pd.DataFrame(data)

# Ensure numeric columns are correct (crucial for plotting)
if '{input.x_axis}' in df.columns:
    df['{input.x_axis}'] = pd.to_numeric(df['{input.x_axis}'], errors='coerce')
if '{input.y_axis}' and '{input.y_axis}' in df.columns:
    df['{input.y_axis}'] = pd.to_numeric(df['{input.y_axis}'], errors='coerce')

# Generate chart based on type
if '{input.chart_type}'.lower() == 'bar' and '{input.y_axis}':
    fig = px.bar(df, x='{input.x_axis}', y='{input.y_axis}', title='{input.title}')
elif '{input.chart_type}'.lower() == 'line' and '{input.y_axis}':
    fig = px.line(df, x='{input.x_axis}', y='{input.y_axis}', title='{input.title}')
elif '{input.chart_type}'.lower() == 'histogram':
    fig = px.histogram(df, x='{input.x_axis}', title='{input.title}')
else:
    # Fallback to scatter if type is complex or data is missing
    fig = px.scatter(df, x='{input.x_axis}', y='{input.y_axis}' if '{input.y_axis}' else None, title='{input.title}')

# Display/Save the figure
# In a real system, this would save fig to S3 and return the URI.
# For simplicity, we just return the fig display code.
fig.show() 
"""
        return code

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous execution: generates code."""
        try:
            parsed_input = self.input_schema.model_validate(input_data)
            df = pd.DataFrame(parsed_input.data)
            
            # 1. Validation sơ bộ
            if df.empty or parsed_input.x_axis not in df.columns:
                raise ToolExecutionError("Data is empty or required X-axis column is missing.")

            # 2. Sinh mã
            code = self._generate_plotly_code(df, parsed_input)
            
            return VisualizerOutput(python_code=code, success=True).model_dump()
        
        except Exception as e:
            return VisualizerOutput(
                python_code=f"# Visualization failed: {e.__class__.__name__}: {str(e)}",
                success=False
            ).model_dump()

    async def async_run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Asynchronous execution wrapper."""
        # Vì đây là CPU-bound (Pandas/Code Generation), ta có thể gọi sync
        return self.run(input_data)