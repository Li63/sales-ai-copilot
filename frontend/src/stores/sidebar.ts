import { defineStore } from 'pinia'
import { getData, postData, postFormData } from '../api/client'
import { getCurrentExternalContact } from '../api/wecom'

export interface CustomerTag {
  tag_name: string
  tag_type: string
  source: string
  confidence: number
}

export interface FollowRecord {
  id: number
  content: string
  next_follow_time: string
  created_at: string
}

export interface Customer {
  id: number
  external_userid: string
  nickname: string
  avatar?: string
  remark?: string
  intention_level: string
  category: string
  intention_score: number
  last_chat_time?: string
  core_demand?: string
  objection?: string
  persona_profile?: string
  persona_updated_at?: string
  tags: CustomerTag[]
  recent_follow_records?: FollowRecord[]
}

export interface Analysis {
  core_demand: string
  objection: string
  reply_suggestions: string[]
  reply_explanations: string[]
  next_action: string
  new_tags: string[]
}

export interface IntentReply {
  reply_suggestion: string
  reply_explanation: string
  next_action: string
}

export interface FeedbackRecord {
  id: number
  original_customer_question: string
  ai_reply: string
  customer_feedback: string
  customer_reply: string
  sales_review: string
  outcome: 'good' | 'bad' | 'neutral'
  lesson: string
  created_at: string
}

export interface PersonaSource {
  id: number
  source_type: string
  title: string
  content: string
  persona_summary: string
  created_at: string
}

export interface IpContentRecord {
  id: number
  theme: string
  channel: string
  content: string
  created_at: string
}

export interface CompanyMaterial {
  id: number
  title: string
  source_type: string
  scope: string
  approval_status: string
  effective: boolean
  tenant_id?: number
  owner_user_id?: number
  content: string
  created_at: string
}

export interface Tenant {
  id: number
  name: string
  contact_name: string
  contact_phone: string
  status: string
  sales_count?: number
  created_at: string
}

export interface TenantOverview {
  tenant: Tenant
  sales_count: number
  material_count: number
  pending_sales: number
  pending_materials: number
  approval_enforcement: boolean
}

export interface FollowOverviewCustomer {
  external_userid: string
  nickname: string
  category: string
  intention_score: number
  last_chat_time?: string
}

export interface FollowOverviewItem {
  customer: FollowOverviewCustomer
  followed_today: boolean
  last_follow: FollowRecord | null
  next_suggestion: string
  hook_suggestion: string
}

export interface FollowOverview {
  date: string
  done: FollowOverviewItem[]
  pending: FollowOverviewItem[]
}

export interface UserProfile {
  id: number
  username: string
  display_name: string
  sales_userid: string
  role: 'platform_admin' | 'tenant_admin' | 'sales'
  tenant_id?: number
  tenant_name: string
  approval_status: string
  industry: string
  customer_group: string
  sales_guide: string
  memory_summary: string
}

export const useSidebarStore = defineStore('sidebar', {
  state: () => ({
    salesUserId: import.meta.env.VITE_DEV_SALES_USERID || 'sales-dev-001',
    externalUserId: '',
    token: localStorage.getItem('sales_ai_token') || '',
    user: null as UserProfile | null,
    customer: null as Customer | null,
    customers: [] as Customer[],
    analysis: null as Analysis | null,
    followRecords: [] as FollowRecord[],
    followOverview: null as FollowOverview | null,
    feedbackRecords: [] as FeedbackRecord[],
    personaSources: [] as PersonaSource[],
    ipContents: [] as IpContentRecord[],
    companyMaterials: [] as CompanyMaterial[],
    tenants: [] as Tenant[],
    tenantOverview: null as TenantOverview | null,
    tenantSales: [] as UserProfile[],
    softwareGuide: '',
    dailyIpAdvice: '',
    busyMessage: '',
    loading: false,
    error: ''
  }),
  getters: {
    customersByCategory: (state) => {
      const groups: Record<string, Customer[]> = { S: [], A: [], B: [], C: [], D: [] }
      for (const customer of state.customers) {
        const category = customer.category || customer.intention_level || 'C'
        if (!groups[category]) groups[category] = []
        groups[category].push(customer)
      }
      return groups
    }
  },
  actions: {
    async register(username: string, password: string, displayName: string, role = 'sales', tenantName = '') {
      const data = await postData<{ token: string; user: UserProfile }>('/api/account/register', {
        username,
        password,
        display_name: displayName,
        role,
        tenant_name: tenantName
      })
      this.setSession(data.token, data.user)
    },
    async login(username: string, password: string) {
      const data = await postData<{ token: string; user: UserProfile }>('/api/account/login', { username, password })
      this.setSession(data.token, data.user)
    },
    async loadMe() {
      if (!this.token) return
      const user = await getData<UserProfile>('/api/account/me')
      this.setSession(this.token, user)
    },
    async saveGuide(industry: string, customerGroup: string) {
      const user = await postData<UserProfile>('/api/account/guide', {
        industry,
        customer_group: customerGroup
      })
      this.setSession(this.token, user)
    },
    logout() {
      this.token = ''
      this.user = null
      this.customer = null
      this.customers = []
      this.analysis = null
      this.followRecords = []
      this.followOverview = null
      this.feedbackRecords = []
      this.personaSources = []
      this.ipContents = []
      this.companyMaterials = []
      this.tenants = []
      this.tenantOverview = null
      this.tenantSales = []
      this.softwareGuide = ''
      this.dailyIpAdvice = ''
      this.busyMessage = ''
      localStorage.removeItem('sales_ai_token')
    },
    setSession(token: string, user: UserProfile) {
      this.token = token
      this.user = user
      this.salesUserId = user.sales_userid
      localStorage.setItem('sales_ai_token', token)
    },
    async bootstrap() {
      this.loading = true
      this.error = ''
      try {
        await this.loadMe()
        if (this.user) {
          this.salesUserId = this.user.sales_userid
        }
        if (this.user?.role === 'platform_admin') {
          await this.loadPlatformTenants()
          return
        }
        if (this.user?.role === 'tenant_admin') {
          await Promise.all([this.loadTenantOverview(), this.loadTenantSales(), this.loadCompanyMaterials()])
          return
        }
        this.externalUserId = await getCurrentExternalContact()
        if (this.user?.sales_guide) {
          await this.loadAnalysis()
          await Promise.all([
            this.loadFollowRecords(),
            this.loadFollowOverview(),
            this.loadCustomers(),
            this.loadFeedback(),
            this.loadPersonaSources(),
            this.loadIpContents(),
            this.loadCompanyMaterials(),
            this.loadSoftwareGuide(),
            this.loadDailyIpAdvice()
          ])
        }
      } catch (error) {
        this.error = error instanceof Error ? error.message : '加载失败'
      } finally {
        this.loading = false
      }
    },
    async loadCustomers() {
      if (!this.token) return
      this.customers = await getData<Customer[]>('/api/customer/list')
    },
    async createCustomer(nickname: string) {
      const customer = await postData<Customer>('/api/customer/create', { nickname })
      this.externalUserId = customer.external_userid
      this.customer = customer
      await Promise.all([
        this.loadAnalysis(),
        this.loadFollowRecords(),
        this.loadFollowOverview(),
        this.loadCustomers(),
        this.loadFeedback(),
        this.loadPersonaSources()
      ])
    },
    async selectCustomer(externalUserId: string) {
      this.externalUserId = externalUserId
      const matched = this.customers.find((item) => item.external_userid === externalUserId)
      if (matched) this.customer = matched
      await Promise.all([this.loadAnalysis(), this.loadFollowRecords(), this.loadFeedback(), this.loadPersonaSources()])
    },
    async loadAnalysis() {
      const data = await getData<{ customer: Customer; analysis: Analysis }>('/api/analysis/realtime', {
        sales_userid: this.salesUserId,
        external_userid: this.externalUserId
      })
      this.customer = data.customer
      this.analysis = data.analysis
    },
    async refreshAnalysis() {
      this.busyMessage = 'AI 正在重新生成回复策略，会结合最新客户画像、聊天习惯和反馈复盘...'
      try {
        await this.loadAnalysis()
      } finally {
        this.busyMessage = ''
      }
    },
    async generateIntentReply(intent: string) {
      this.busyMessage = 'AI 正在把你的推进意图转成客户更容易接受的话术...'
      try {
        return await postData<IntentReply>('/api/analysis/intent-reply', {
          sales_userid: this.salesUserId,
          external_userid: this.externalUserId,
          intent
        })
      } finally {
        this.busyMessage = ''
      }
    },
    async loadFollowRecords() {
      this.followRecords = await getData<FollowRecord[]>('/api/follow/list', {
        sales_userid: this.salesUserId,
        external_userid: this.externalUserId
      })
    },
    async loadFollowOverview() {
      if (!this.token) return
      this.followOverview = await getData<FollowOverview>('/api/follow/overview')
    },
    async addFollow(content: string) {
      await postData('/api/follow/add', {
        sales_userid: this.salesUserId,
        external_userid: this.externalUserId,
        content
      })
      await Promise.all([this.loadFollowRecords(), this.loadFollowOverview(), this.loadCustomers()])
    },
    async importTranscript(transcript: string, customerName?: string) {
      await postData('/api/chat/import', {
        sales_userid: this.salesUserId,
        external_userid: this.externalUserId,
        transcript,
        customer_name: customerName
      })
      await Promise.all([this.loadAnalysis(), this.loadFollowRecords(), this.loadFollowOverview(), this.loadCustomers()])
    },
    async loadFeedback() {
      this.feedbackRecords = await getData<FeedbackRecord[]>('/api/feedback/list', {
        sales_userid: this.salesUserId,
        external_userid: this.externalUserId
      })
    },
    async addFeedback(payload: {
      ai_reply: string
      customer_reply: string
      sales_review: string
      outcome: 'good' | 'bad' | 'neutral'
      original_customer_question?: string
    }) {
      await postData<FeedbackRecord>('/api/feedback/add', {
        sales_userid: this.salesUserId,
        external_userid: this.externalUserId,
        ...payload
      })
      await Promise.all([this.loadFeedback(), this.loadAnalysis()])
    },
    async loadPersonaSources() {
      this.personaSources = await getData<PersonaSource[]>('/api/persona/source/list', {
        sales_userid: this.salesUserId,
        external_userid: this.externalUserId
      })
    },
    async addPersonaSource(payload: { title: string; content: string; source_type: string }) {
      await postData<PersonaSource>('/api/persona/source/add', {
        sales_userid: this.salesUserId,
        external_userid: this.externalUserId,
        ...payload
      })
      await Promise.all([this.loadPersonaSources(), this.loadAnalysis()])
    },
    async loadIpContents() {
      if (!this.token) return
      this.ipContents = await getData<IpContentRecord[]>('/api/ip/content/list')
    },
    async generateIpContent(theme: string, channel = 'moments') {
      await postData<IpContentRecord>('/api/ip/content/generate', { theme, channel })
      await this.loadIpContents()
    },
    async refreshDailyIpAdvice() {
      this.busyMessage = 'AI 正在刷新今日个人 IP 建议，重新结合行业、客户群体和销售指南...'
      try {
        await this.loadDailyIpAdvice()
      } finally {
        this.busyMessage = ''
      }
    },
    async loadDailyIpAdvice() {
      if (!this.token) return
      const data = await getData<{ content: string; date: string }>('/api/ip/daily-advice')
      this.dailyIpAdvice = data.content
    },
    async loadCompanyMaterials() {
      if (!this.token) return
      this.companyMaterials = await getData<CompanyMaterial[]>('/api/company/material/list')
    },
    async addCompanyMaterial(payload: { title: string; content: string; source_type: string; scope?: string }) {
      await postData<CompanyMaterial>('/api/company/material/add', payload)
      if (this.user?.role === 'sales') {
        await Promise.all([this.loadCompanyMaterials(), this.loadAnalysis()])
        return
      }
      await Promise.all([this.loadCompanyMaterials(), this.loadTenantOverview()])
    },
    async loadPlatformTenants() {
      this.tenants = await getData<Tenant[]>('/api/platform/tenants')
    },
    async createTenant(payload: { name: string; contact_name?: string; contact_phone?: string }) {
      await postData<Tenant>('/api/platform/tenants', payload)
      await this.loadPlatformTenants()
    },
    async createTenantAdmin(payload: { tenant_id: number; username: string; password: string; display_name?: string }) {
      await postData<UserProfile>('/api/platform/tenant-admins', { ...payload, role: 'tenant_admin' })
      await this.loadPlatformTenants()
    },
    async updateTenantStatus(tenantId: number, status: string) {
      await postData<Tenant>(`/api/platform/tenants/${tenantId}/status`, { status })
      await this.loadPlatformTenants()
    },
    async loadTenantOverview() {
      this.tenantOverview = await getData<TenantOverview>('/api/tenant/overview')
    },
    async loadTenantSales() {
      this.tenantSales = await getData<UserProfile[]>('/api/tenant/sales')
    },
    async createTenantSales(payload: { username: string; password: string; display_name?: string }) {
      await postData<UserProfile>('/api/tenant/sales', payload)
      await Promise.all([this.loadTenantSales(), this.loadTenantOverview()])
    },
    async updateSalesStatus(userId: number, status: string) {
      await postData<UserProfile>(`/api/tenant/sales/${userId}/status`, { status })
      await Promise.all([this.loadTenantSales(), this.loadTenantOverview()])
    },
    async updateMaterialStatus(materialId: number, status: string) {
      await postData<CompanyMaterial>(`/api/tenant/materials/${materialId}/status`, { status })
      await Promise.all([this.loadCompanyMaterials(), this.loadTenantOverview()])
    },
    async loadSoftwareGuide() {
      if (!this.token) return
      const data = await getData<{ content: string }>('/api/guide/software')
      this.softwareGuide = data.content
    },
    async extractFiles(purpose: 'chat' | 'persona' | 'company', files: FileList | File[]) {
      const formData = new FormData()
      formData.append('purpose', purpose)
      Array.from(files).forEach((file) => formData.append('files', file))
      const purposeLabel = purpose === 'chat' ? '聊天记录文件' : purpose === 'persona' ? '客户资料文件' : '公司资料文件'
      this.busyMessage = `AI 正在解析${purposeLabel}，Word/PDF 会先提取文字，图片会连续识别，请稍等...`
      try {
        const data = await postFormData<{ text: string; count: number; purpose: string }>('/api/file/extract', formData)
        return data.text
      } finally {
        this.busyMessage = ''
      }
    },
    async extractImages(purpose: 'chat' | 'persona' | 'company', files: FileList | File[]) {
      return this.extractFiles(purpose, files)
    }
  }
})
