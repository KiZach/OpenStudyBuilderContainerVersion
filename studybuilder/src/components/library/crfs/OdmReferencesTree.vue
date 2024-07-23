<template>
  <div>
    <v-card>
      <v-card-title v-if="!noTitle">
        <span class="dialog-title">{{ $t('OdmViewer.odm_references') }}</span>
      </v-card-title>
      <v-row v-show="loading" center justify="center">
        <v-col cols="12" sm="4">
          <v-progress-circular
            color="primary"
            indeterminate
            size="128"
            class="ml-4"
          />
        </v-col>
      </v-row>
      <v-card-text v-show="!loading">
        <v-treeview
          :key="graphKey"
          :items="crfData"
          activatable
          density="compact"
          item-value="name"
          disabled
          :open-all="openAll"
          :active="activeNodes"
        >
          <template #prepend="{ prepItem }">
            <v-icon :color="iconTypeAndColor(prepItem).color">
              {{ iconTypeAndColor(prepItem).type }}
            </v-icon>
          </template>
          <template #label="{ lblItem }">
            <div v-if="lblItem" class="black--text">
              {{ lblItem.name }}
            </div>
          </template>
        </v-treeview>
      </v-card-text>
      <v-card-actions v-if="!noActions">
        <v-spacer />
        <v-btn class="secondary-btn" color="white" @click="close()">
          {{ $t('_global.close') }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </div>
</template>

<script>
import crfs from '@/api/crfs'

export default {
  props: {
    item: {
      type: Object,
      default: null,
    },
    type: {
      type: String,
      default: null,
    },
    noTitle: {
      type: Boolean,
      default: false,
    },
    noActions: {
      type: Boolean,
      default: false,
    },
    fullData: {
      type: Boolean,
      default: true,
    },
    openAll: {
      type: Boolean,
      default: true,
    },
  },
  emits: ['close'],
  data() {
    return {
      templates: [],
      forms: [],
      groups: [],
      items: [],
      crfData: [],
      graphKey: 0,
      loading: false,
      activeNodes: [],
    }
  },
  watch: {
    item(value) {
      if (value) {
        this.fetchData()
      }
    },
    openAll() {
      this.graphKey += 1
    },
  },
  mounted() {
    this.fetchData()
  },
  methods: {
    close() {
      this.templates = []
      this.forms = []
      this.groups = []
      this.items = []
      this.crfData = []
      this.$emit('close')
    },
    iconTypeAndColor(item) {
      if (item) {
        if (item.template) {
          return { type: 'mdi-alpha-t-circle-outline', color: 'primary' }
        } else if (item.form) {
          return { type: 'mdi-alpha-f-circle-outline', color: 'success' }
        } else if (item.group) {
          return { type: 'mdi-alpha-g-circle-outline', color: 'secondary' }
        } else {
          return { type: 'mdi-alpha-i-circle-outline', color: 'error' }
        }
      } else {
        return {}
      }
    },
    async getCrfData() {
      this.loading = true
      this.crfTreeData = []
      const params = {}
      await crfs.get('study-events', { params }).then((resp) => {
        this.templates = resp.data.items
        for (const template of this.templates) {
          this.templates[this.templates.indexOf(template)].template = true
        }
      })
      await crfs.get('forms', { params }).then((resp) => {
        this.forms = resp.data.items
        for (const form of this.forms) {
          this.forms[this.forms.indexOf(form)].form = true
        }
      })
      await crfs.get('item-groups', { params }).then((resp) => {
        this.groups = resp.data.items
        for (const group of this.groups) {
          this.groups[this.groups.indexOf(group)].group = true
        }
      })
      this.crfData = [this.item]
      this.groups = this.groups.filter((group) =>
        group.items.some((item) => item.uid === this.item.uid)
      )
      for (const group of this.groups) {
        this.groups[this.groups.indexOf(group)].children = [this.item]
      }
      if (this.groups.length > 0) {
        this.crfData = this.groups
      } else {
        this.loading = false
        this.graphKey += 1
        return
      }
      this.forms = this.forms.filter((form) =>
        this.groups.some((group) =>
          form.item_groups.some((g) => g.uid === group.uid)
        )
      )
      for (const form of this.forms) {
        this.forms[this.forms.indexOf(form)].children = this.forms[
          this.forms.indexOf(form)
        ].item_groups.map((group) =>
          this.groups.find((el) => el.uid === group.uid)
        )
        this.forms[this.forms.indexOf(form)].children = this.forms[
          this.forms.indexOf(form)
        ].children.filter(function (val) {
          return val !== undefined
        })
      }
      if (this.forms.length > 0) {
        this.crfData = this.forms
      } else {
        this.loading = false
        this.graphKey += 1
        return
      }
      this.templates = this.templates.filter((template) =>
        this.forms.some((form) =>
          template.forms.some((g) => g.uid === form.uid)
        )
      )
      for (const template of this.templates) {
        this.templates[this.templates.indexOf(template)].children =
          this.templates[this.templates.indexOf(template)].forms.map((form) =>
            this.forms.find((el) => el.uid === form.uid)
          )
        this.templates[this.templates.indexOf(template)].children =
          this.templates[this.templates.indexOf(template)].children.filter(
            function (val) {
              return val !== undefined
            }
          )
      }
      if (this.templates.length > 0) {
        this.crfData = this.templates
      }
      this.loading = false
      this.graphKey += 1
    },
    async getTemplates(form) {
      await crfs.getRelationships(form.uid, 'forms').then((resp) => {
        this.templates = resp.data.OdmTemplate
      })
      if (this.templates) {
        const params = {
          filters: {
            uid: { v: this.templates },
          },
        }
        await crfs.get('study-events', { params }).then((resp) => {
          this.templates = resp.data.items
        })
      }
    },
    async getForms(template, group) {
      if (template) {
        const params = {
          filters: {
            uid: {
              v: Array.from(template.forms.map((f) => (f.uid ? f.uid : f))),
            },
          },
        }
        await crfs.get('forms', { params }).then((resp) => {
          this.forms = resp.data.items
        })
      } else {
        await crfs.getRelationships(group.uid, 'item-groups').then((resp) => {
          this.forms = resp.data.OdmForm
        })
      }
    },
    async getGroups(form, item) {
      if (form) {
        const params = {
          filters: {
            uid: {
              v: Array.from(form.item_groups.map((f) => (f.uid ? f.uid : f))),
            },
          },
        }
        await crfs.get('item-groups', { params }).then((resp) => {
          this.groups = resp.data.items
        })
      } else {
        await crfs.getRelationships(item.uid, 'items').then((resp) => {
          this.groups = resp.data.OdmItemGroup
        })
      }
    },
    async getDataFromTemplateLevel() {
      this.loading = true
      this.crfData = [
        {
          name: this.item.name,
          uid: this.item.uid,
          children: [],
          template: true,
        },
      ]
      await this.getForms(this.item, null)
      this.crfData[0].children = this.forms
      for (const form of this.crfData[0].children) {
        await this.getGroups(form, null)
        for (const group of this.groups) {
          this.groups[this.groups.indexOf(group)] = {
            name: group.name,
            uid: group.uid,
            children: group.items,
            group: true,
          }
        }
        const index = this.crfData[0].children.indexOf(form)
        this.crfData[0].children[index] = {
          name: form.name,
          uid: form.uid,
          children: this.groups,
          form: true,
        }
      }
      this.loading = false
      this.graphKey += 1
    },
    async getDataFromFormLevel() {
      this.loading = true
      await this.getGroups(this.item, null)
      const dataFromForm = [
        {
          name: this.item.name,
          uid: this.item.uid,
          children: this.groups,
          form: true,
        },
      ]
      this.crfData = dataFromForm
      if (dataFromForm[0].children && dataFromForm[0].children.length > 0) {
        for (const group of dataFromForm[0].children) {
          const index = dataFromForm[0].children.indexOf(group)
          dataFromForm[0].children[index] = {
            name: group.name,
            uid: group.uid,
            children: group.items,
            group: true,
          }
        }
      }
      if (this.fullData) {
        await this.getTemplates(this.item)
        if (this.templates && this.templates.length > 0) {
          this.crfData = this.templates
          for (const el of this.crfData) {
            this.crfData[this.crfData.indexOf(el)] = {
              name: el.name,
              uid: el.uid,
              children: dataFromForm,
              template: true,
            }
          }
        }
      }
      this.loading = false
      this.graphKey += 1
    },
    async getDataFromGroupLevel() {
      this.loading = true
      const dataFromGroup = [
        {
          name: this.item.name,
          uid: this.item.uid,
          children: this.item.items,
          group: true,
        },
      ]
      this.crfData = dataFromGroup
      if (this.fullData) {
        await this.getForms(null, this.item)
        if (this.forms && this.forms.length > 0) {
          const forms = {
            forms: this.forms,
          }
          await this.getForms(forms, null)
          for (const form of this.forms) {
            this.forms[this.forms.indexOf(form)] = {
              name: form.name,
              uid: form.uid,
              children: dataFromGroup,
              form: true,
            }
          }
          this.crfData = this.forms
          for (const form of this.forms) {
            await this.getTemplates(form)
            if (this.templates && this.templates.length > 0) {
              this.crfData = []
              for (const template of this.templates) {
                this.crfData.push({
                  name: template.name,
                  uid: template.uid,
                  children: [form],
                  template: true,
                })
              }
            }
          }
        }
        const output = []
        this.crfData.forEach(function (item) {
          const existing = output.filter(function (v) {
            return v.name === item.name
          })
          if (existing.length) {
            const existingIndex = output.indexOf(existing[0])
            output[existingIndex].children = output[
              existingIndex
            ].children.concat(item.children)
          } else {
            output.push(item)
          }
        })
        this.crfData = output
      }
      this.loading = false
      this.graphKey += 1
    },
    fetchData() {
      this.activeNodes = [this.item.name]
      if (this.type === 'template') {
        this.getDataFromTemplateLevel()
      } else if (this.type === 'form') {
        this.getDataFromFormLevel()
      } else if (this.type === 'group') {
        this.getDataFromGroupLevel()
      } else if (this.type === 'item') {
        this.getCrfData()
      }
    },
  },
}
</script>
<style scoped>
.highlight {
  background-color: lightblue;
}
</style>
