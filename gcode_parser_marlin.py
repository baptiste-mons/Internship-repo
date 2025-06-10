import os
import re
import matplotlib.pyplot as plt
from collections import defaultdict

class CodeAnalyzer:
    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.directive_counts = defaultdict(int)
        self.defined_macros = set()
        self.undefined_macros = defaultdict(int)
        self.condition_stack = []
        self.files_analyzed = 0

        # Pour les G-code
        self.gcode_stats = defaultdict(int)
        self.gcode_instructions = []

    def analyze_codebase(self):
        for subdir, _, files in os.walk(self.root_dir):
            for file in files:
                if file.endswith(('.c', '.h')):
                    file_path = os.path.join(subdir, file)
                    self.analyze_file(file_path)
                    self.files_analyzed += 1

        print(f"\nAnalyzed {self.files_analyzed} files.")
        self.visualize_results()

        if self.gcode_stats:
            print("\nG-code Instruction Summary:")
            for instr, count in sorted(self.gcode_stats.items(), key=lambda x: x[1], reverse=True):
                print(f"{instr:>4}: {count}")
        else:
            print("\nNo G-code instructions found.")

    def analyze_file(self, file_path: str):
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                for line_num, line in enumerate(file, 1):
                    line = line.strip()

                    # Analyse directives préprocesseur
                    self._analyze_directive(line, file_path, line_num)

                    # Recherche de G-code (dans TOUTES les lignes, y compris commentées)
                    self._analyze_gcode_line(line, file_path, line_num)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    def _analyze_directive(self, line: str, file_path: str, line_num: int):
        directive_match = re.match(r'#\s*(ifdef|ifndef|if|elif|else|endif|define|undef)\b\s*(\w+)?', line)
        if directive_match:
            directive = directive_match.group(1)
            macro = directive_match.group(2)

            self.directive_counts[directive] += 1

            if directive == 'define' and macro:
                self.defined_macros.add(macro)
            elif directive == 'undef' and macro:
                self.defined_macros.discard(macro)
            elif directive in {'ifdef', 'ifndef'} and macro:
                if macro not in self.defined_macros:
                    self.undefined_macros[macro] += 1

            if directive in {'ifdef', 'ifndef', 'if'}:
                self.condition_stack.append((directive, macro, file_path, line_num))
            elif directive == 'endif':
                if self.condition_stack:
                    self.condition_stack.pop()

    def _analyze_gcode_line(self, line: str, file_path: str, line_num: int):
        matches = re.findall(r'\bG([0-9]{1,2})\b', line)
        for match in matches:
            gcode = f"G{match}"
            self.gcode_stats[gcode] += 1
            self.gcode_instructions.append({
                "instruction": gcode,
                "file": file_path,
                "line": line_num,
                "full_line": line
            })

    def visualize_results(self):
        plt.figure(figsize=(18, 10))

        # 1. Histogramme des directives
        plt.subplot(1, 3, 2)
        keys = list(self.directive_counts.keys())
        values = [self.directive_counts[k] for k in keys]
        plt.bar(keys, values, color='skyblue')
        plt.title("Preprocessor Directives Frequency")
        plt.xlabel("Directive")
        plt.ylabel("Count")

        """         
        # 2. Macros définies
        plt.subplot(2, 3, 2)
        macro_lengths = [len(m) for m in self.defined_macros]
        plt.hist(macro_lengths, bins=range(1, max(macro_lengths) + 2), color='orange', edgecolor='black')
        plt.title("Length of Defined Macros")
        plt.xlabel("Length")
        plt.ylabel("Frequency") """

        """         
        # 3. Macros non définies utilisées
        plt.subplot(2, 3, 3)
        if self.undefined_macros:
            top_undef = sorted(self.undefined_macros.items(), key=lambda x: x[1], reverse=True)[:10]
            plt.barh([x[0] for x in top_undef], [x[1] for x in top_undef], color='tomato')
            plt.title("Top 10 Undefined Macros Used")
            plt.xlabel("Occurrences") """

        """         
        # 4. Profondeur des #if imbriqués
        plt.subplot(2, 3, 4)
        if self.condition_stack:
            depths = [len(self.condition_stack)]
        else:
            depths = [0]
        plt.bar(['Max Depth'], [max(depths)], color='purple')
        plt.title("Max Nested Conditional Depth") """

        # 5. Nombre de fichiers analysés
        plt.subplot(1, 3, 1)
        plt.bar(['Files'], [self.files_analyzed], color='green')
        plt.title("Files Analyzed")

        # 6. Instructions G-code
        if self.gcode_stats:
            plt.subplot(1, 3, 3)
            sorted_gcodes = sorted(self.gcode_stats.items(), key=lambda x: x[1], reverse=True)[:15]
            plt.barh([g[0] for g in sorted_gcodes], [g[1] for g in sorted_gcodes], color='limegreen')
            plt.title("Top G-code Instructions")
            plt.xlabel("Occurrences")

        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Analyze C code for preprocessor directives and G-code mentions.")
    parser.add_argument("path", help="Path to the root directory of the codebase.")
    args = parser.parse_args()

    analyzer = CodeAnalyzer(args.path)
    analyzer.analyze_codebase()
