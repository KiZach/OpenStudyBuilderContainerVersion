<template>
  <HorizontalStepperForm
    ref="stepper"
    :title="$t('CrfConditionForm.set_condition')"
    :steps="steps"
    :form-observer-getter="getObserver"
    @close="close"
    @save="submit"
  >
    <template #[`step.condition`]="{ step }">
      <v-form :ref="`observer_${step}`">
        <v-card elevation="4" class="mx-auto pa-4 mb-4">
          <div class="text-h5 mb-4">
            {{ $t('CRFForms.definition') }}
          </div>
          <v-row>
            <v-col cols="6">
              <v-text-field
                v-model="form.oid"
                :label="$t('CRFForms.oid')"
                data-cy="form-oid"
                density="compact"
                clearable
              />
            </v-col>
            <v-col cols="6">
              <v-text-field
                v-model="form.name"
                :label="$t('CRFForms.name') + '*'"
                data-cy="form-oid-name"
                :rules="[formRules.required]"
                density="compact"
                clearable
              />
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="9">
              <div class="subtitle-2 text--disabled">
                {{ $t('CRFForms.help_for_sponsor') }}
              </div>
              <VueEditor
                v-model="engDescription.sponsor_instruction"
                :toolbar="customToolbar"
                :placeholder="$t('CRFForms.help_for_sponsor')"
              />
            </v-col>
          </v-row>
        </v-card>
      </v-form>
    </template>
    <template #[`step.description`]="{ step }">
      <v-form :ref="`observer_${step}`">
        <CrfDescriptionTable
          :key="descKey"
          :edit-descriptions="desc"
          @set-desc="setDesc"
        />
      </v-form>
    </template>
    <template #[`step.expression`]="{ step }">
      <v-form :ref="`observer_${step}`">
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.formal_expressions[0].context"
              :label="$t('CrfConditionForm.context')"
              :rules="[formRules.required]"
              density="compact"
              clearable
              class="mt-3"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-textarea
              v-model="form.formal_expressions[0].expression"
              :label="$t('CrfConditionForm.formal_expression')"
              :rules="[formRules.required]"
              density="compact"
              clearable
              class="mt-6"
            />
          </v-col>
        </v-row>
        <div
          v-for="(expression, index) in expressionsArray"
          :key="expression.index"
        >
          <div v-if="!form.uid">
            <v-row>
              <v-col>
                <v-autocomplete
                  v-model="expressionsArray[index].elementType"
                  :label="$t('CrfConditionForm.nested_element')"
                  :items="nestedElements"
                  density="compact"
                  clearable
                  @change="setFormalExpression()"
                />
              </v-col>
              <v-col>
                <v-autocomplete
                  v-model="expressionsArray[index].element"
                  :items="
                    expressionsArray[index].elementType === 'Form'
                      ? crfForms
                      : expressionsArray[index].elementType === 'Item Group'
                        ? crfGroups
                        : crfItems
                  "
                  :disabled="!expressionsArray[index].elementType"
                  item-title="name"
                  item-value="oid"
                  return-object
                  density="compact"
                  clearable
                  @change="setFormalExpression()"
                />
              </v-col>
              <v-col cols="2">
                <v-autocomplete
                  v-model="expressionsArray[index].separator"
                  :label="$t('CrfConditionForm.separator')"
                  :items="separators"
                  density="compact"
                  clearable
                  @change="setFormalExpression()"
                />
              </v-col>
            </v-row>
            <v-row
              v-show="
                expressionsArray[index].elementType === 'Item' &&
                expressionsArray[index].element &&
                expressionsArray[index].element.codelist
              "
              :key="key"
            >
              <v-col>
                {{ $t('CrfConditionForm.select_value') }}
              </v-col>
              <v-col>
                <v-autocomplete
                  :key="key"
                  v-model="expressionsArray[index].value"
                  label="Value"
                  :items="expressionsArray[index].terms"
                  item-title="name"
                  item-value="name"
                  density="compact"
                  clearable
                  :loading="!expressionsArray[index].terms"
                  @change="setFormalExpression()"
                />
              </v-col>
            </v-row>
          </div>
        </div>
        <v-btn
          v-if="!form.uid"
          size="small"
          data-cy="create-new-sponsor-values"
          color="primary"
          icon="mdi-plus-circle-outline"
          @click="addExpression"
        />
      </v-form>
    </template>
  </HorizontalStepperForm>
</template>

<script>
import crfs from '@/api/crfs'
import CrfDescriptionTable from '@/components/library/crfs/CrfDescriptionTable.vue'
import HorizontalStepperForm from '@/components/tools/HorizontalStepperForm.vue'
import constants from '@/constants/libraries'
import { VueEditor } from 'vue3-editor-js'
import { useAppStore } from '@/stores/app'
import { computed } from 'vue'

export default {
  components: {
    HorizontalStepperForm,
    CrfDescriptionTable,
    VueEditor,
  },
  inject: ['eventBusEmit', 'formRules'],
  props: {
    itemToLink: {
      type: Object,
      default: null,
    },
    crfForms: {
      type: Array,
      default: null,
    },
    crfGroups: {
      type: Array,
      default: null,
    },
    crfItems: {
      type: Array,
      default: null,
    },
    crfGroup: {
      type: Object,
      default: null,
    },
  },
  emits: ['cancel', 'close'],
  setup() {
    const appStore = useAppStore()

    return {
      userData: computed(() => appStore.userData),
    }
  },
  data() {
    return {
      helpItems: [],
      form: {
        oid: 'C.',
        formal_expressions: [
          {
            library_name: 'Sponsor',
            context: 'XPath',
          },
        ],
        alias_uids: [],
      },
      descriptionUids: [],
      steps: [
        { name: 'condition', title: this.$t('CrfConditionForm.condition') },
        {
          name: 'description',
          title: this.$t('CRFForms.description_details'),
          belowDisplay: true,
        },
        {
          name: 'expression',
          title: this.$t('CrfConditionForm.formal_expression'),
        },
      ],
      desc: [],
      nestedElements: ['Form', 'Item Group', 'Item'],
      expressionsArray: [{ index: 0 }],
      separators: ['AND', 'OR'],
      key: 0,
      terms: [],
      descKey: 0,
      engDescription: { library_name: 'Sponsor', language: 'ENG' },
      customToolbar: [
        ['bold', 'italic', 'underline'],
        [{ script: 'sub' }, { script: 'super' }],
        [{ list: 'ordered' }, { list: 'bullet' }],
      ],
    }
  },
  watch: {
    itemToLink() {
      this.initiateSteps()
    },
  },
  mounted() {
    this.initiateSteps()
  },
  methods: {
    initiateSteps() {
      this.initForm()
      if (!this.userData.multilingual) {
        this.steps = this.steps.filter(function (obj) {
          return obj.name !== 'description'
        })
      } else {
        this.steps.splice(1, 0, {
          name: 'description',
          title: this.$t('CRFForms.description_details'),
          belowDisplay: true,
        })
      }
      const uniqueSteps = Array.from(
        new Set(this.steps.map((a) => a.name))
      ).map((name) => {
        return this.steps.find((a) => a.name === name)
      })
      this.steps = uniqueSteps
    },
    setFormalExpression() {
      const itemDef = 'ItemDef'
      const itemGroupDef = 'ItemGroupDef'
      const formDef = 'FormDef'
      const oid = '[@OID='
      const value = '[@Value='
      this.form.formal_expressions[0].expression = '../'
      this.expressionsArray.forEach((el, index) => {
        if (el.elementType === 'Form' && el.element) {
          this.form.formal_expressions[0].expression +=
            formDef +
            oid +
            el.element.oid +
            (el.separator ? `] ${el.separator} ../` : ']/')
        }
        if (el.elementType === 'Item Group' && el.element) {
          this.form.formal_expressions[0].expression +=
            itemGroupDef +
            oid +
            el.element.oid +
            (el.separator ? `] ${el.separator} ../` : ']/')
        }
        if (el.elementType === 'Item' && el.element) {
          this.form.formal_expressions[0].expression +=
            itemDef +
            oid +
            el.element.oid +
            ']' +
            value +
            el.value +
            (el.separator ? `] ${el.separator} ../` : ']')
          this.expressionsArray[index].terms = el.element.terms
        }
      })
      if (
        this.form.formal_expressions[0].expression[
          this.form.formal_expressions[0].length - 1
        ] === '/'
      ) {
        this.form.formal_expressions[0].expression =
          this.form.formal_expressions[0].slice(0, -1)
      }
    },
    addExpression() {
      this.expressionsArray.push({ index: this.expressionsArray.length })
    },
    setDesc(desc) {
      this.desc = desc
    },
    getObserver(step) {
      return this.$refs[`observer_${step}`]
    },
    close() {
      this.form = {
        oid: 'C.',
        formal_expressions: [
          {
            library_name: 'Sponsor',
            context: 'XPath',
          },
        ],
        alias_uids: [],
      }
      this.desc = []
      this.engDescription = { library_name: 'Sponsor', language: 'ENG' }
      this.expressionsArray = [{ index: 0 }]
      this.descKey += 1
      this.$refs.stepper.reset()
      this.$emit('cancel')
    },
    async submit() {
      await this.createOrUpdateDescription()
      this.form.library_name = constants.LIBRARY_SPONSOR
      if (this.form.oid === 'C.') {
        this.form.oid = ''
      }
      try {
        if (this.form.uid) {
          this.form.formal_expressions[0].change_description = ''
          crfs.editCondition(this.form.uid, this.form).then(() => {
            this.close()
            this.$emit('close')
          })
        } else if (this.itemToLink.parentFormUid) {
          await crfs.createCondition(this.form).then((resp) => {
            const data = [this.itemToLink]
            data[0].collection_exception_condition_oid = resp.data.oid
            crfs
              .addItemGroupsToForm(data, this.itemToLink.parentFormUid, false)
              .then(() => {
                this.close()
                this.$emit('close')
              })
          })
        } else if (this.itemToLink.parentGroupUid) {
          await crfs.createCondition(this.form).then((resp) => {
            const data = [this.itemToLink]
            data[0].collection_exception_condition_oid = resp.data.oid
            crfs
              .addItemsToItemGroup(data, this.itemToLink.parentGroupUid, false)
              .then(() => {
                this.close()
                this.$emit('close')
              })
          })
        }
      } finally {
        this.$refs.stepper.loading = false
      }
    },
    async createOrUpdateDescription() {
      const descArray = []
      this.desc.forEach((e) => {
        if (e.uid) {
          descArray.push(e)
        } else {
          e.library_name = constants.LIBRARY_SPONSOR
          descArray.push(e)
        }
      })
      if (!this.engDescription.name) {
        this.engDescription.name = this.form.name
      }
      descArray.push(this.engDescription)
      this.form.descriptions = descArray
    },
    initForm() {
      if (
        this.itemToLink.collection_exception_condition_oid &&
        this.itemToLink.collection_exception_condition_oid !== 'null' &&
        this.itemToLink.collection_exception_condition_oid !== 'none'
      ) {
        const data = {}
        data.filters = `{"oid":{ "v": ["${this.itemToLink.collection_exception_condition_oid}"], "op": "co" }}`
        crfs.getConditionByOid(data).then((resp) => {
          this.engDescription = resp.data.items[0].descriptions.find(
            (el) => el.language === 'ENG'
          )
          this.desc = resp.data.items[0].descriptions.filter(
            (el) => el.language !== 'ENG'
          )
          this.form = resp.data.items[0]
          this.form.alias_uids = []
          this.descKey += 1
        })
      }
    },
  },
}
</script>
