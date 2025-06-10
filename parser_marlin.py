import re
from collections import defaultdict
import os
import argparse
import matplotlib.pyplot as plt
from typing import Dict, List, Set

class CPPVariabilityAnalyzer:
    def __init__(self):
        self.features: Set[str] = set()
        self.variation_points: List[Dict] = []
        self.directive_stats = {
            "ifdef": 0,
            "ifndef": 0,
            "if": 0,
            "else": 0,
            "elif": 0
        }
        self.file_complexity = defaultdict(int)
        self.feature_scattering = defaultdict(int)

    def analyze_file(self, file_path: str):
        current_nesting = 0
        nesting_stack = []

        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            for line_num, line in enumerate(file, 1):
                line = line.strip()
                if not line or not line.startswith('#'):
                    continue

                # Process all directive types
                if line.startswith("#ifdef"):
                    self._process_directive(line, line_num, file_path, "ifdef", current_nesting)
                    current_nesting += 1
                    nesting_stack.append(current_nesting)
                elif line.startswith("#ifndef"):
                    self._process_directive(line, line_num, file_path, "ifndef", current_nesting)
                    current_nesting += 1
                    nesting_stack.append(current_nesting)
                elif line.startswith("#if"):
                    self._process_directive(line, line_num, file_path, "if", current_nesting)
                    current_nesting += 1
                    nesting_stack.append(current_nesting)
                elif line.startswith("#else"):
                    self._process_directive(line, line_num, file_path, "else", current_nesting)
                    self.directive_stats["else"] += 1
                elif line.startswith("#elif"):
                    self._process_directive(line, line_num, file_path, "elif", current_nesting)
                    self.directive_stats["elif"] += 1
                elif line.startswith("#endif"):
                    if nesting_stack:
                        nesting_stack.pop()
                        current_nesting = nesting_stack[-1] if nesting_stack else 0

    def _process_directive(self, line: str, line_num: int, file_path: str, 
                         directive_type: str, nesting_depth: int):
        # Extract condition and features
        condition = line.split(maxsplit=1)[1] if len(line.split()) > 1 else ""
        features = self._extract_features(condition)
        
        # Update statistics
        self.directive_stats[directive_type] += 1
        self.file_complexity[file_path] += 1
        
        # Record variation point
        vp = {
            "type": directive_type,
            "line": line_num,
            "file": file_path,
            "condition": condition,
            "features": features,
            "nesting": nesting_depth
        }
        self.variation_points.append(vp)
        
        # Update feature tracking
        for feature in features:
            self.features.add(feature)
            self.feature_scattering[feature] += 1

    def _extract_features(self, condition: str) -> Set[str]:
        # Extract all valid feature names from condition
        pattern = r'\bdefined\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)|([A-Za-z_][A-Za-z0-9_]*)'
        matches = re.findall(pattern, condition)
        return {m[0] or m[1] for m in matches if (m[0] or m[1]) and not (m[0] or m[1]).isdigit()}

    def visualize_results(self):
        plt.figure(figsize=(18, 12))
        
        # Plot 1: Directive Type Distribution
        plt.subplot(2, 3, 1)
        types, counts = zip(*sorted(self.directive_stats.items()))
        plt.bar(types, counts, color=['blue', 'orange', 'green', 'red', 'purple'])
        plt.title("Directive Type Distribution")
        plt.ylabel("Count")
        
        # Plot 2: Feature Scattering
        plt.subplot(2, 3, 2)
        top_features = sorted(self.feature_scattering.items(), 
                            key=lambda x: x[1], reverse=True)[:15]
        plt.barh([f[0] for f in top_features], [f[1] for f in top_features], color='teal')
        plt.title("Top 15 Features by Scattering")
        plt.xlabel("Files Affected")
        
        # Plot 3: File Complexity
        plt.subplot(2, 3, 3)
        complex_files = sorted(self.file_complexity.items(), 
                             key=lambda x: x[1], reverse=True)[:15]
        plt.barh([os.path.basename(f[0]) for f in complex_files], 
                [f[1] for f in complex_files], color='salmon')
        plt.title("Top 15 Complex Files")
        plt.xlabel("Variation Points")
        
        # Plot 4: Nesting Depth Distribution
        plt.subplot(2, 3, 4)
        nesting_depths = [vp["nesting"] for vp in self.variation_points]
        max_depth = max(nesting_depths) if nesting_depths else 0
        plt.hist(nesting_depths, bins=range(0, max_depth + 2), 
                color='skyblue', edgecolor='black')
        plt.title("Nesting Depth Distribution")
        plt.xlabel("Nesting Level")
        plt.ylabel("Count")
        
        # Plot 5: Features per Directive Type
        plt.subplot(2, 3, 5)
        features_per_type = defaultdict(int)
        for vp in self.variation_points:
            if vp["features"]:
                features_per_type[vp["type"]] += 1
        plt.bar(features_per_type.keys(), features_per_type.values(), color='gold')
        plt.title("Directives Containing Features")
        plt.ylabel("Count")
        
        plt.tight_layout()
        plt.show()

def analyze_codebase(path: str):
    analyzer = CPPVariabilityAnalyzer()
    
    if os.path.isfile(path):
        analyzer.analyze_file(path)
    elif os.path.isdir(path):
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith(('.c', '.cpp', '.h', '.hpp')):
                    analyzer.analyze_file(os.path.join(root, file))
    
    # Print summary statistics
    print("\n=== Variability Analysis Summary ===")
    print(f"Total Features Found: {len(analyzer.features)}")
    print(f"Total Variation Points: {len(analyzer.variation_points)}")
    print("\nDirective Statistics:")
    for dtype, count in analyzer.directive_stats.items():
        print(f"{dtype.upper():>6}: {count}")
    
    analyzer.visualize_results()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="C/C++ Preprocessor Variability Analyzer")
    parser.add_argument("path", help="Path to file or directory")
    args = parser.parse_args()
    
    analyze_codebase(args.path)