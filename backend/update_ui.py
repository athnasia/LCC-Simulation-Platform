import re

with open('../frontend/src/views/engineering/LccReportView.vue', 'r', encoding='utf-8') as f:
    content = f.read()

# Task 1: Donut chart graphic
graphic_pattern = r"(graphic:\s*\[\s*\{\s*type:\s*'text',\s*left:\s*)'center'(,\s*top:\s*)'38%'(,\s*style:\s*\{\s*text:\s*'全生命周期成本净现值',\s*fill:\s*'#94A3B8',\s*font:\s*'400 16px Inter, sans-serif',\s*align:\s*)'center'(,\s*\}\s*\},)"
content = re.sub(graphic_pattern, r"\1'80%'\2'10%'\3'right'\4", content)

graphic_pattern_2 = r"(\{\s*type:\s*'text',\s*left:\s*)'center'(,\s*top:\s*)'46%'(,\s*style:\s*\{\s*text:\s*'¥ ' \+ dynamicTotalCost\.value\.toLocaleString\('zh-CN', \{ minimumFractionDigits: 2, maximumFractionDigits: 2 \}\),\s*fill:\s*'#F8FAFC',\s*font:\s*'700 32px Inter, sans-serif',\s*align:\s*)'center'(,\s*\}\s*\},\s*\])"
content = re.sub(graphic_pattern_2, r"\1'80%'\2'15%'\3'right'\4", content)

# Task 2: Data specs move
collapse_pattern = r'(\s*<el-collapse class="data-specs-collapse">[\s\S]*?</el-collapse>)'
match = re.search(collapse_pattern, content)
if match:
    collapse_html = match.group(1)
    # Remove from original place
    content = content.replace(collapse_html, '')
    
    # Insert below header-right tag
    header_right_pattern = r'(<div class="header-right">\s*<el-tag class="status-tag" type="success" effect="plain" color="#1E293B">\s*✅ 仿真已完成\s*</el-tag>)'
    new_header_right = r'\1\n' + collapse_html.strip()
    content = re.sub(header_right_pattern, new_header_right, content)

# Task 3: 4 items in one row
content = re.sub(r'<el-col :xs="24" :sm="12"( class="mt-24")?>', r'<el-col :xs="24" :sm="12" :lg="6">', content)

with open('../frontend/src/views/engineering/LccReportView.vue', 'w', encoding='utf-8') as f:
    f.write(content)

print('Update script finished.')
