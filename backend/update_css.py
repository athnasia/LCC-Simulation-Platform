import re

with open('../frontend/src/views/engineering/LccReportView.vue', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace donut label
content = re.sub(r'label: \{\s*show: true,\s*color: \'#e8f0ff\',\s*formatter: \(params: any\) => `\$\{params\.name\}\\n\$\{params\.percent\}%`,\s*\},',
                 '''label: {
            show: true,
            color: '#F8FAFC',
            formatter: (params: any) => `${params.name} ${params.percent}%`,
          },''', content)

# Replace itemStyle borderColor
content = re.sub(r'borderColor: \'#0b1324\'', 'borderColor: \'#0F172A\'', content)

# Replace Cashflow Axis
content = re.sub(r'xAxis: \{\s*type: \'category\',\s*data: xAxisData,\s*axisLine: \{ lineStyle: \{ color: gridLineColor \} \},\s*axisLabel: \{ color: chartMutedTextColor, interval: 0 \},\s*\},',
                 '''xAxis: {
      type: 'category',
      data: xAxisData,
      axisLine: { lineStyle: { color: '#334155' } },
      axisLabel: { 
        color: '#94A3B8', 
        interval: (index: number, value: string) => {
          if (value === 'Year 0' || value === 'Year 5' || value === 'Year 10' || value === 'Year 15') return true
          return false
        }
      },
    },''', content)

content = re.sub(r'nameTextStyle: \{ color: chartMutedTextColor, padding: \[0, 0, 8, 0\] \},',
                 'nameTextStyle: { color: \'#94A3B8\', padding: [0, 0, 8, 0] },', content)
                 
content = re.sub(r'axisLabel: \{\s*color: chartMutedTextColor,\s*formatter: \(value: number\) => .*?,\s*\},',
                 '''axisLabel: {
        color: '#94A3B8',
        formatter: (value: number) => `¥${(value / 10000).toFixed(0)}w`,
      },''', content)

css_new = """<style scoped>
.lcc-report-view {
  min-height: calc(100vh - 64px);
  background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
  color: #F8FAFC;
  padding: 32px;
  font-family: 'Inter', 'Noto Sans SC', sans-serif;
  position: relative;
}

.lcc-report-view::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image: 
    linear-gradient(rgba(71, 85, 105, 0.1) 1px, transparent 1px),
    linear-gradient(90deg, rgba(71, 85, 105, 0.1) 1px, transparent 1px);
  background-size: 40px 40px;
  pointer-events: none;
}

.report-shell {
  max-width: 1600px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 32px;
  position: relative;
  z-index: 1;
}

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.back-button {
  width: fit-content;
  color: #94A3B8;
}

.back-button:hover {
  color: #F8FAFC;
}

.title-block h1 {
  margin: 0 0 8px 0;
  font-size: 28px;
  font-weight: 700;
  color: #F8FAFC;
  display: flex;
  align-items: center;
  gap: 16px;
}

.snapshot-code {
  font-size: 14px;
  font-weight: 400;
  color: #94A3B8;
  padding: 4px 12px;
  background: rgba(51, 65, 85, 0.4);
  border-radius: 4px;
}

.title-subline {
  color: #94A3B8;
  font-size: 14px;
}

.conclusion-panel {
  background: rgba(30, 41, 59, 0.8);
  border: 1px solid #334155;
  border-radius: 8px;
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.conclusion-title {
  font-size: 16px;
  font-weight: 600;
  color: #10B981;
}

.conclusion-text {
  font-size: 14px;
  line-height: 1.6;
  color: #F8FAFC;
}

.conclusion-text .highlight {
  font-weight: 700;
  color: #3B82F6;
}

.hero-metrics {
  margin-top: 0;
}

.metric-card {
  background: #1E293B;
  border: 1px solid #334155;
  border-radius: 8px;
  padding: 24px;
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.financial-capex { border-top: 2px solid #3B82F6; }
.financial-opex { border-top: 2px solid #10B981; }
.financial-mr { border-top: 2px solid #F59E0B; }
.financial-risk { border-top: 2px solid #8B5CF6; }
.financial-eol { border-top: 2px solid #A78BFA; }

.metric-label {
  color: #94A3B8;
  font-size: 16px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 6px;
}

.warn-icon {
  color: #F59E0B;
  font-size: 16px;
  cursor: help;
}

.info-icon {
  color: #3B82F6;
  font-size: 16px;
  cursor: help;
}

.metric-value {
  color: #F8FAFC;
  font-size: 36px;
  font-weight: 700;
  line-height: 1.2;
}

.metric-subtitle {
  color: #64748B;
  font-size: 12px;
}

.energy-metrics {
  margin-bottom: 0;
}

.energy-card {
  border-top: none;
  justify-content: center;
}

.energy-lcoe {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, #1E293B 100%);
  border: 1px solid rgba(59, 130, 246, 0.3);
}

.energy-lcoe .metric-value {
  font-size: 40px;
  color: #3B82F6;
}

.unit-text {
  font-size: 16px;
  font-weight: 400;
  color: #94A3B8;
  margin-left: 4px;
}

.mt-24 {
  margin-top: 24px;
}

.chart-card, .audit-card {
  background: #1E293B;
  border: 1px solid #334155;
  border-radius: 8px;
  padding: 24px;
}

.chart-header {
  margin-bottom: 24px;
}

.chart-header h3 {
  margin: 0 0 4px 0;
  font-size: 20px;
  font-weight: 600;
  color: #F8FAFC;
}

.chart-header span {
  font-size: 14px;
  color: #94A3B8;
}

.chart-canvas {
  height: 320px;
  width: 100%;
}

.chart-canvas-wide {
  height: 320px;
}

.chart-insight {
  margin-top: 16px;
  padding: 12px 16px;
  background: rgba(15, 23, 42, 0.5);
  border-radius: 4px;
  font-size: 13px;
  color: #94A3B8;
  line-height: 1.5;
}

.audit-table {
  --el-table-border-color: #334155;
  --el-table-header-bg-color: rgba(15, 23, 42, 0.8);
  --el-table-header-text-color: #F8FAFC;
  --el-table-tr-bg-color: #1E293B;
  --el-table-row-hover-bg-color: rgba(51, 65, 85, 0.5);
  --el-table-text-color: #F8FAFC;
  border-radius: 4px;
}

.el-table--striped .el-table__body tr.el-table__row--striped td.el-table__cell {
  background: rgba(15, 23, 42, 0.3);
}

.total-cell {
  color: #3B82F6;
  font-weight: 700;
}

.data-specs-collapse {
  --el-collapse-border-color: #334155;
  --el-collapse-header-bg-color: #1E293B;
  --el-collapse-header-text-color: #F8FAFC;
  --el-collapse-content-bg-color: #1E293B;
  --el-collapse-content-text-color: #94A3B8;
  border: 1px solid #334155;
  border-radius: 8px;
  overflow: hidden;
}

.collapse-title {
  font-size: 16px;
  font-weight: 600;
  padding-left: 16px;
}

.specs-list {
  padding: 0 24px 16px 40px;
  margin: 0;
  line-height: 2;
  font-size: 13px;
}

@media (min-width: 1200px) {
  .col-lg-5 {
    max-width: 20%;
    flex: 0 0 20%;
  }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 60vh;
  gap: 24px;
}
</style>"""

content = re.sub(r'<style scoped>.*?</style>', css_new, content, flags=re.DOTALL)

with open('../frontend/src/views/engineering/LccReportView.vue', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done")
