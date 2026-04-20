/**
 * 金额格式化工具函数
 */

/**
 * 格式化金额显示
 * @param value 金额数值
 * @param currency 货币符号，默认 '¥'
 * @param decimals 小数位数，默认 2
 */
export function formatMoney(value: number | string | null, currency = '¥', decimals = 2): string {
  if (value === null || value === undefined) return `${currency} --`
  const num = typeof value === 'string' ? parseFloat(value) : value
  if (isNaN(num)) return `${currency} --`
  return `${currency}${num.toLocaleString('zh-CN', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })}`
}

/**
 * 格式化百分比
 * @param value 百分比值（如 0.0523 表示 5.23%）
 * @param decimals 小数位数，默认 2
 */
export function formatPercent(value: number | null, decimals = 2): string {
  if (value === null || value === undefined) return '--%'
  return `${(value * 100).toFixed(decimals)}%`
}

/**
 * 盈亏颜色类名
 * 正数返回 'pnl-positive' (红)，负数返回 'pnl-negative' (绿)，零返回 ''
 */
export function pnlColorClass(value: number | null): string {
  if (value === null || value === undefined || value === 0) return ''
  return value > 0 ? 'pnl-positive' : 'pnl-negative'
}
