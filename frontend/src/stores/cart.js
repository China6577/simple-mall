import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import cartApi from '@/api/cart'

/**
 * 购物车状态管理。
 *
 * 维护购物车条目列表、摘要信息，并提供增删改查动作。
 * 登录后调用 loadCart() 即可从后端同步最新数据。
 */
export const useCartStore = defineStore('cart', () => {
  // State
  const items = ref([])
  const summary = ref({
    total_count: 0,
    selected_count: 0,
    total_amount: 0,
  })
  const loading = ref(false)

  // Getters
  const selectedItems = computed(() => items.value.filter((item) => item.selected))
  const totalCount = computed(() => summary.value.total_count || 0)
  const selectedCount = computed(() => summary.value.selected_count || 0)
  const totalAmount = computed(() => summary.value.total_amount || 0)
  const isAllSelected = computed(
    () => items.value.length > 0 && items.value.every((item) => item.selected)
  )

  /**
   * 根据当前 items 重新计算摘要，避免每次小改动都全量拉取后端。
   */
  function recalcSummary() {
    let totalCount = 0
    let selectedCount = 0
    let totalAmount = 0
    for (const item of items.value) {
      totalCount += Number(item.quantity) || 0
      if (item.selected) {
        selectedCount += Number(item.quantity) || 0
        totalAmount += Number(item.subtotal) || 0
      }
    }
    summary.value = {
      total_count: totalCount,
      selected_count: selectedCount,
      total_amount: Number(totalAmount.toFixed(2)),
    }
  }

  // Actions
  async function loadCart() {
    loading.value = true
    try {
      const data = await cartApi.getCart()
      items.value = data.items || []
      summary.value = data.summary || { total_count: 0, selected_count: 0, total_amount: 0 }
    } finally {
      loading.value = false
    }
  }

  async function addToCart(skuId, quantity = 1) {
    await cartApi.addToCart({ sku_id: skuId, quantity })
    await loadCart()
  }

  async function updateItem(itemId, data) {
    const updated = await cartApi.updateItem(itemId, data)
    const index = items.value.findIndex((item) => item.id === itemId)
    if (index !== -1) {
      items.value[index] = updated
    }
    recalcSummary()
    return updated
  }

  async function removeItem(itemId) {
    await cartApi.removeItem(itemId)
    items.value = items.value.filter((item) => item.id !== itemId)
    recalcSummary()
  }

  async function selectAll(selected) {
    const ids = items.value.map((item) => item.id)
    if (ids.length === 0) return
    await cartApi.batchSelect({ item_ids: ids, selected })
    items.value.forEach((item) => {
      item.selected = selected
    })
    recalcSummary()
  }

  function clearCart() {
    items.value = []
    summary.value = { total_count: 0, selected_count: 0, total_amount: 0 }
  }

  return {
    items,
    summary,
    loading,
    selectedItems,
    totalCount,
    selectedCount,
    totalAmount,
    isAllSelected,
    loadCart,
    addToCart,
    updateItem,
    removeItem,
    selectAll,
    clearCart,
  }
})
