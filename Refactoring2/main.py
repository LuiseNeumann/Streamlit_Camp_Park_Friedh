#from src.data_processing import data_loader
#from src.utils.geometry_utils import GeometryProcessor
#from src.utils.calculations import WorkforceCalculator
from src.visualization.layer_management import LayerManager
from src.visualization.map_builder import MapBuilder
#from src.visualization.popup_content import PopupCreator
from src.data_processing.data_loader import DataLoader
from config.settings import Config

import logging
from pathlib import Path
from typing import Dict, Any
import pandas as pd
import geopandas as gpd
from fuzzywuzzy import fuzz, process


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('parks_visualization.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ParksVisualizationApp:
    """Main application class for Parks Visualization."""
    
    def __init__(self):
        self.data_loader = DataLoader()
        self.map_builder = MapBuilder()
        self.map_builder.layer_management = LayerManager()
        logger.info("Initialized Parks Visualization Application")
    
    def load_all_data(self) -> Dict[str, Any]:
        """Load all required data for visualization."""
        logger.info("Loading all data sources...")
        
        # Load main datasets
        parks_data = self.data_loader.load_parks_data()
        cemetery_data = self.data_loader.load_cemetery_data()
        cities_data = self.data_loader.load_cities_data()
        federal_states_data = self.data_loader.load_federal_states_data()
        heatmap_data = self.data_loader.load_heatmap_data()
        camping_data = self.data_loader.load_camping_data()
        camping_heatmap_data = self.data_loader.load_heatmap_camping_data()
        
        return {
            "parks": parks_data,
            "cemetery": cemetery_data,
            "cities": cities_data,
            "federal_states": federal_states_data,
            "heatmap": heatmap_data,
            "camping": camping_data,
            "camping_heatmap": camping_heatmap_data

        }
    
    def create_main_map(self, data: Dict[str, Any], size_threshold: float = None) -> str:
        """
        Create the main Germany map with all layers.
        
        Args:
            data: Dictionary containing all loaded data
            size_threshold: Size threshold for marker categorization
            
        Returns:
            Path to the saved map file
        """
        try:
            size_threshold = size_threshold or Config.DEFAULT_SIZE_THRESHOLD
            logger.info(f"Creating main map with size threshold: {size_threshold}")
            
            # Build the main map
            main_map = self.map_builder.build_main_map(
                parks_data=data["parks"],
                cemetery_data=data["cemetery"],
                camping_data=data["camping"],
                cities_data=data["cities"],
                federal_states_data=data["federal_states"],
                heatmap_data=data["heatmap"],
                camping_heatmap_data=data["camping_heatmap"],
                size_threshold=size_threshold
            )
        
            # Save the map
            output_path = Config.OUTPUT_DIR / "germany_map.html"
            main_map.save(str(output_path))
            logger.info(f"Main map saved to: {output_path}")
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error creating main map: {e}")
            raise
    
    def create_bundesland_maps(self, data: Dict[str, Any], size_threshold: float = None) -> Dict[str, str]:
        """
        Create individual maps for each federal state.
        
        Args:
            data: Dictionary containing all loaded data
            size_threshold: Size threshold for marker categorization
            
        Returns:
            Dictionary mapping federal state names to map file paths
        """
        try:
            size_threshold = size_threshold or Config.DEFAULT_SIZE_THRESHOLD
            bundesland_maps = {}
            
            if data["federal_states"]["gdf"].empty:
                logger.warning("No federal states data available")
                return bundesland_maps
            
            # Get unique federal states
            federal_states = data["federal_states"]["gdf"]["NAME_1"].unique()
            logger.info(f"Creating maps for {len(federal_states)} federal states")
            
            for bundesland in federal_states:
                try:
                    # Filter data for this federal state
                    parks_filtered = self._filter_data_by_bundesland(
                        data["parks"]["gdf"], bundesland
                    )
                    cemetery_filtered = self._filter_data_by_bundesland(
                        data["cemetery"]["gdf"], bundesland
                    )
                    camping_filtered = self._filter_data_by_bundesland(
                        data["camping"]["gdf"], bundesland
                    )
                    # Get federal state geometry
                    bundesland_geometry = data["federal_states"]["gdf"][
                        data["federal_states"]["gdf"]["NAME_1"] == bundesland
                    ]
                    
                    # Create the map
                    bundesland_map = self.map_builder.build_bundesland_map(
                        bundesland=bundesland,
                        parks_data=parks_filtered,
                        cemetery_data=cemetery_filtered,
                        camping_data=camping_filtered,
                        bundesland_geometry=bundesland_geometry,
                        size_threshold=size_threshold
                    )
                    
                    # Save the map
                    safe_name = bundesland.replace(" ", "_").replace("/", "_")
                    output_path = Config.OUTPUT_DIR / f"{safe_name}.html"
                    bundesland_map.save(str(output_path))
                    
                    bundesland_maps[bundesland] = str(output_path)
                    logger.info(f"Created map for {bundesland}: {output_path}")
                    
                except Exception as e:
                    logger.error(f"Error creating map for {bundesland}: {e}")
                    continue
            
            return bundesland_maps
            
        except Exception as e:
            logger.error(f"Error creating federal state maps: {e}")
            raise
    
    def _filter_data_by_bundesland(self, gdf, bundesland_name: str):
        """Filter GeoDataFrame by federal state name"""

        try:
            if gdf.empty or 'bundesland' not in gdf.columns:
                logger.warning(f"No 'bundesland' column found in data with columns: {gdf.columns.tolist()}")
                return gdf.iloc[0:0]
            
            return gdf[gdf['bundesland'] == bundesland_name].copy()
            
        except Exception as e:
            logger.error(f"Error filtering data for {bundesland_name}: {e}")
            return gdf.iloc[0:0]
    
    def run(self, size_threshold: float = None, create_bundesland_maps: bool = True) -> Dict[str, Any]:
        """
        Run the complete visualization pipeline.
        
        Args:
            size_threshold: Size threshold for marker categorization
            create_bundesland_maps: Whether to create individual federal state maps
            
        Returns:
            Dictionary with paths to created maps
        """
        try:
            logger.info("Starting Parks Visualization pipeline...")
            
            # Load all data
            data = self.load_all_data()
            
            # Validate data
            if data["parks"]["df"].empty and data["cemetery"]["df"].empty:
                logger.error("No parks or cemetery data loaded. Cannot create maps.")
                return {"error": "No data available"}
            
            results = {}
            
            # Create main map
            logger.info("Creating main Germany map...")
            main_map_path = self.create_main_map(data, size_threshold)
            results["main_map"] = main_map_path
            
            # Create federal state maps if requested
            if create_bundesland_maps:
                logger.info("Creating federal state maps...")
                bundesland_maps = self.create_bundesland_maps(data, size_threshold)
                results["bundesland_maps"] = bundesland_maps
            
            # Log summary
            total_parks = len(data["parks"]["df"])
            total_cemeteries = len(data["cemetery"]["df"])
            total_cities = len(data["cities"]) if not data["cities"].empty else 0
            total_camping =len(data["camping"])
            
            logger.info(f"""
            Visualization completed successfully!
            - Total parks: {total_parks}
            - Total cemeteries: {total_cemeteries}
            - Total cities: {total_cities}
            - Total camping: {total_camping}
            - Main map: {main_map_path}
            - Federal state maps: {len(results.get('bundesland_maps', {}))}
            """)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in visualization pipeline: {e}")
            raise


def main():
    """Main entry point."""
    try:
        # Initialize application
        app = ParksVisualizationApp()
        
        # Run visualization with default settings
        results = app.run(
            size_threshold=Config.DEFAULT_SIZE_THRESHOLD,
            create_bundesland_maps=True
        )
        
        if "error" in results:
            print(f"Error: {results['error']}")
            return 1
        
        # Print results
        print("\n" + "="*50)
        print("PARKS VISUALIZATION COMPLETED")
        print("="*50)
        print(f"Main map: {results['main_map']}")
        
        if "bundesland_maps" in results:
            print(f"\nFederal state maps ({len(results['bundesland_maps'])}):")
            for state, path in results['bundesland_maps'].items():
                print(f"  - {state}: {path}")
        
        print(f"\nAll files saved to: {Config.OUTPUT_DIR}")
        print("="*50)
        
        return 0
        
    except Exception as e:
        logger.error(f"Application failed: {e}")
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())


