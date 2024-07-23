<template>
  <v-card>
    <v-card-title>
      {{ $t('CrfDuplicationForm.duplicate') }}
    </v-card-title>
    <v-card-text>
      <v-form ref="observer">
        <v-row>
          <v-col v-if="type !== crfTypes.ITEM" cols="2">
            <v-checkbox
              v-model="relations"
              :label="$t('CrfDuplicationForm.include')"
              class="mt-6 ml-2"
            />
          </v-col>
          <v-col v-if="type !== crfTypes.ITEM" cols="10">
            <OdmReferencesTree
              :item="item"
              :type="type"
              no-title
              no-actions
              :full-data="false"
              :open-all="relations"
            />
          </v-col>
        </v-row>
        <v-row>
          <div class="ml-4">
            {{ $t('CrfDuplicationForm.attributes') }}
          </div>
        </v-row>
        <v-row>
          <v-col cols="4">
            <v-text-field
              v-model="name"
              :label="$t('_global.name')"
              density="compact"
              clearable
              :rules="[formRules.required]"
            />
          </v-col>
          <v-col cols="4">
            <v-text-field
              v-model="oid"
              :label="$t('_global.oid')"
              density="compact"
              clearable
            />
          </v-col>
          <v-col cols="4">
            <v-autocomplete
              v-if="type !== crfTypes.TEMPLATE"
              v-model="itemToLinkTo"
              :items="itemsToLinkTo"
              :label="$t('CrfDuplicationForm.item_to_link')"
              item-title="name"
              item-value="uid"
              density="compact"
              clearable
              :rules="[formRules.required]"
              return-object
            />
          </v-col>
        </v-row>
      </v-form>
    </v-card-text>
    <v-card-actions>
      <v-spacer />
      <v-btn class="primary" @click="save()">
        {{ $t('_global.save') }}
      </v-btn>
      <v-btn class="secondary-btn" color="white" @click="close()">
        {{ $t('_global.close') }}
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script>
import OdmReferencesTree from '@/components/library/crfs/OdmReferencesTree.vue'
import crfs from '@/api/crfs'
import crfTypes from '@/constants/crfTypes'

export default {
  components: {
    OdmReferencesTree,
  },
  props: {
    open: Boolean,
    item: {
      type: Object,
      default: null,
    },
    type: {
      type: String,
      default: null,
    },
  },
  emits: ['close'],
  inkect: ['formRules'],
  data() {
    return {
      relations: false,
      name: '',
      oid: '',
      form: {},
      itemsToLinkTo: [],
      itemToLinkTo: null,
    }
  },
  watch: {
    type() {
      this.getElementsToLinkTo()
    },
  },
  created() {
    this.crfTypes = crfTypes
  },
  mounted() {
    this.getElementsToLinkTo()
  },
  methods: {
    getElementsToLinkTo() {
      if (this.type === crfTypes.FORM) {
        crfs.get('study-events', {}).then((resp) => {
          this.itemsToLinkTo = resp.data.items
        })
      } else if (this.type === crfTypes.GROUP) {
        crfs.getCrfForms().then((resp) => {
          this.itemsToLinkTo = resp.data
        })
      } else if (this.type === crfTypes.ITEM) {
        crfs.getCrfGroups().then((resp) => {
          this.itemsToLinkTo = resp.data
        })
      }
    },
    close() {
      this.$emit('close')
    },
    async save() {
      const { valid } = await this.$refs.observer.validate()
      if (!valid) return
      let resp
      this.form = Object.assign(this.form, this.item)
      this.form.name = this.name
      this.form.oid = this.oid
      if (this.type === crfTypes.TEMPLATE) {
        resp = await crfs.createTemplate(this.form)
        if (this.relations) {
          await crfs.addFormsToTemplate(this.item.forms, resp.data.uid, true)
        }
        this.close()
      } else if (this.type === crfTypes.FORM) {
        this.form.alias_uids = this.form.aliases.map((alias) => alias.uid)
        resp = await crfs.createForm(this.form)
        this.form.uid = resp.uid
        if (this.relations) {
          crfs.addItemGroupsToForm(this.item.item_groups, resp.data.uid, true)
        }
        await crfs.addFormsToTemplate([this.form], this.itemToLinkTo.uid, false)
        this.close()
      } else if (this.type === crfTypes.GROUP) {
        this.form.alias_uids = this.form.aliases.map((alias) => alias.uid)
        this.form.sdtm_domain_uids = this.form.sdtm_domains.map(
          (sdtm) => sdtm.uid
        )
        resp = await crfs.createItemGroup(this.form)
        this.form.uid = resp.uid
        if (this.relations) {
          crfs.addItemsToItemGroup(this.item.items, resp.data.uid, true)
        }
        await crfs.addItemGroupsToForm(
          [this.form],
          this.itemToLinkTo.uid,
          false
        )
        this.close()
      } else {
        this.form.alias_uids = this.form.aliases.map((alias) => alias.uid)
        if (this.form.codelist) {
          this.form.codelist_uid = this.form.codelist.uid
        }
        if (this.form.unit_definitions) {
          for (const unit of this.form.unit_definitions) {
            this.form.unit_definitions[
              this.form.unit_definitions.indexOf(unit)
            ].mandatory = unit.mandatory !== null && unit.mandatory !== false
          }
        }
        this.form.terms.forEach((term) => {
          term.uid = term.term_uid
          delete term.term_uid
        })
        resp = await crfs.createItem(this.form)
        this.form.uid = resp.uid
        crfs.addItemsToItemGroup([this.form], this.itemToLinkTo.uid, false)
        this.close()
      }
    },
  },
}
</script>
