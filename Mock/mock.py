from fpdf import FPDF
import json
import textwrap

gap_entry_summary = 50

class BasePDF(FPDF):
    def header(self):
        self.set_font("Arial", style="B", size=16)
        self.set_text_color(255, 255, 255)
        self.set_fill_color(0, 102, 204)
        self.cell(0, 10, "Weekly Report", border=False, ln=True, align="C", fill=True)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", size=8)
        self.set_text_color(169, 169, 169)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

class PDFGenerator:
    def __init__(self):
        self.pdf = BasePDF()
        self.column_widths = [50, 20, 70, 50]
        self.headers = ["Subdomain", "Depth", "All Nameservers", "Issues"]

    def draw_title(self):
        self.pdf.set_font("Arial", style="B", size=14)
        self.pdf.set_text_color(0, 102, 204)
        self.pdf.cell(0, 10, "New Subdomains", ln=True)
        self.pdf.ln(5)

    def draw_header(self):
        self.pdf.set_font("Arial", style="B", size=12)
        self.pdf.set_fill_color(240, 240, 240)
        for header, width in zip(self.headers, self.column_widths):
            self.pdf.cell(width, 10, header, border=1, align="C", fill=True)
        self.pdf.ln()
        self.pdf.set_font("Arial", size=12)

    def draw_cell(self, x, y, width, height, text, align="C"):
        self.pdf.rect(x, y, width, height)
        
        if isinstance(text, str):
            chars_per_line = int(width / (self.pdf.get_string_width('a') * 1.2))
            
            if len(text) > chars_per_line:
                wrapped_text = textwrap.fill(text, width=chars_per_line)
                lines = wrapped_text.split('\n')
                
                line_height = 5 if width == self.column_widths[0] else height / len(lines)
                total_text_height = line_height * len(lines)
                
                start_y = y + (height - total_text_height) / 2
                
                current_y = start_y
                for line in lines:
                    self.pdf.set_xy(x, current_y)
                    self.pdf.cell(width, line_height, line, align=align)
                    current_y += line_height
            else:
                self.pdf.set_xy(x, y + (height/2) - 5)
                self.pdf.cell(width, 10, text, align=align)
        else:
            self.pdf.set_xy(x, y + (height/2) - 5)
            self.pdf.cell(width, 10, str(text), align=align)

    def process_entry(self, entry):
        return {
            'subdomain': entry["subdomain"],
            'depth': str(entry["depth"]),
            'nameservers': "\n".join(entry["all_nameservers"]),
            'issues': self.format_issues(entry["issues"])
        }

    def format_issues(self, issues):
        return "\n".join(issues.values()) if issues else "No Issues"

    def calculate_row_height(self, data):
        line_counts = []
        for text, width in zip(data, self.column_widths):
            if isinstance(text, str):
                chars_per_line = int(width / (self.pdf.get_string_width('a') * 1.2))
                wrapped_text = textwrap.fill(text, width=chars_per_line)
                line_counts.append(len(wrapped_text.split('\n')))
            else:
                line_counts.append(1)
        return max(line_counts) * 10

    # def get_num_lines(self, text, width):
    #     if not text:
    #         return 1
    #     return max(1, len(self.pdf.multi_cell(width, 10, str(text), split_only=True)))

    def check_page_break(self, height):
        if self.pdf.get_y() + height > self.pdf.page_break_trigger:
            self.pdf.add_page()
            self.draw_header()

    def draw_row(self, data, row_height):
        x_start = self.pdf.get_x()
        y_start = self.pdf.get_y()
        
        current_x = x_start
        for text, width in zip(data, self.column_widths):
            self.draw_cell(current_x, y_start, width, row_height, text)
            current_x += width

        self.pdf.set_xy(x_start, y_start + row_height)

    def draw_summary(self, data):
        total_subdomains = len(data)
        domains_with_issues = len([d for d in data if d.get('issues')])
        
        dns_providers = {'awsdns': 0, 'akam': 0, 'ultradns': 0, 'other': 0}
        
        for record in data:
            nameservers = record.get('all_nameservers', [])
            for ns in nameservers:
                ns = ns.lower()
                if 'awsdns' in ns:
                    dns_providers['awsdns'] += 1
                elif 'akam' in ns:
                    dns_providers['akam'] += 1
                elif 'ultradns' in ns:
                    dns_providers['ultradns'] += 1
                else:
                    dns_providers['other'] += 1

        current_y = self.pdf.get_y() + 10
        self.pdf.set_text_color(255, 0, 0)  # Red
        
        self.pdf.set_xy(10, current_y)
        self.pdf.cell(50, 10, "Summary:")
        
        current_y += 10
        self.pdf.set_xy(10, current_y)
        self.pdf.cell(100, 10, f"Total new subdomains: {total_subdomains}")

        current_y += 10

        self.pdf.set_xy(10, current_y)
        self.pdf.cell(100, 10, f"Subdomains with issues: {domains_with_issues}")
        
        current_y += 10
        self.pdf.set_xy(10, current_y)
        self.pdf.cell(100, 10, f"DNS providers are Akamai, AWSDNS, UltraDNS")

        current_y += 10
        self.pdf.set_xy(10, current_y)
        self.pdf.cell(100, 10, f"Numbers of provider nameserver used by new subdomains:")

        current_y += 10
        self.pdf.set_xy(10, current_y)
        self.pdf.cell(100, 10, f"Akamai: {dns_providers['akam']}")

        current_y += 10
        self.pdf.set_xy(10, current_y)
        self.pdf.cell(100, 10, f"AWSDNS: {dns_providers['awsdns']}")

        current_y += 10
        self.pdf.set_xy(10, current_y)
        self.pdf.cell(100, 10, f"UltraDNS: {dns_providers['ultradns']}")



    def generate_report(self, json_file, output_file):
        with open(json_file, 'r') as f:
            json_data = [json.loads(line.strip()) for line in f]

        self.pdf.add_page()
        self.draw_title()
        self.draw_header()

        for entry in json_data:
            processed_data = self.process_entry(entry)
            row_height = self.calculate_row_height(processed_data.values())
            self.check_page_break(row_height)
            self.draw_row(processed_data.values(), row_height)

        self.check_page_break(gap_entry_summary)
        self.draw_summary(json_data) 

        self.pdf.output(output_file)


if __name__ == "__main__":
    pdf_generator = PDFGenerator()
    pdf_generator.generate_report("mock.json", "weekly_report.pdf")
