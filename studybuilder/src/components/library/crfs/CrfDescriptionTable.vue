<template>
  <NNTable
    :headers="headers"
    item-value="uid"
    disable-filtering
    :items="desc"
    hide-export-button
    hide-default-switches
  >
    <template #actions="">
      <v-btn
        class="ml-2"
        fab
        size="small"
        icon="mdi-plus"
        color="primary"
        :label="$t('CRFForms.new_translation')"
        data-cy="form-new-translation"
        :disabled="readOnly || !checkPermission($roles.LIBRARY_WRITE)"
        @click.stop="addLanguage"
      />
    </template>
    <template #[`item.language`]="{ index }">
      <v-autocomplete
        v-model="desc[index].language"
        :items="languages"
        :label="$t('CRFForms.language')"
        data-cy="form-language"
        density="compact"
        :clearable="!readOnly"
        class="mt-3"
        item-title="code_submission_value"
        item-value="code_submission_value"
        :readonly="readOnly"
      />
    </template>
    <template #[`item.name`]="{ item, index }">
      <div :key="descKey">
        <v-autocomplete
          v-if="!desc[index].newDesc"
          v-model="desc[index].name"
          autocomplete="null"
          :label="$t('CRFForms.name')"
          data-cy="form-displayed-text"
          :items="descriptions"
          item-title="name"
          return-object
          :clearable="!readOnly"
          :readonly="readOnly"
          @change="addExistingDescription(item, index)"
        >
          <template #no-data>
            <v-row>
              <v-btn
                size="small"
                color="primary"
                :title="$t('CodelistCreationForm.title')"
                class="mt-3 ml-6 mb-2"
                :disabled="readOnly"
                @click.stop="createNewDescription(index)"
              >
                {{ $t('_global.add_new') }}
              </v-btn>
            </v-row>
          </template>
        </v-autocomplete>
        <v-text-field
          v-else
          v-model="desc[index].name"
          :label="$t('CRFForms.name')"
          data-cy="form-language-name"
          density="compact"
          :clearable="!readOnly"
          class="mt-5"
          autocomplete="null"
          :readonly="readOnly"
        />
      </div>
    </template>
    <template #[`item.desc`]="{ index }">
      <div v-show="readOnly">
        <QuillEditor
          v-model:content="desc[index].description"
          content-type="html"
          :toolbar="customToolbar"
        />
      </div>
      <div v-show="!readOnly">
        <QuillEditor
          v-model:content="desc[index].description"
          content-type="html"
          :toolbar="customToolbar"
          :placeholder="desc[index].uid ? '' : $t('_global.description')"
        />
      </div>
    </template>
    <template #[`item.notes`]="{ index }">
      <div v-show="readOnly">
        <QuillEditor
          v-model:content="desc[index].sponsor_instruction"
          content-type="html"
          :toolbar="customToolbar"
          data-cy="sponsor-instructions"
        />
      </div>
      <div v-show="!readOnly">
        <QuillEditor
          v-model:content="desc[index].sponsor_instruction"
          content-type="html"
          :toolbar="customToolbar"
          :placeholder="desc[index].uid ? '' : $t('CRFForms.impl_notes')"
          data-cy="sponsor-instructions"
        />
      </div>
    </template>
    <template #[`item.inst`]="{ index }">
      <div v-show="readOnly">
        <QuillEditor
          v-model:content="desc[index].instruction"
          content-type="html"
          :toolbar="customToolbar"
          data-cy="description-instructions"
        />
      </div>
      <div v-show="!readOnly">
        <QuillEditor
          v-model:content="desc[index].instruction"
          content-type="html"
          :toolbar="customToolbar"
          :placeholder="
            desc[index].uid ? '' : $t('CRFForms.compl_instructions')
          "
          data-cy="description-instructions"
        />
      </div>
    </template>
    <template #[`item.delete`]="{ index }">
      <v-btn
        v-if="index !== 0"
        icon="mdi-delete-outline"
        class="mt-3"
        :disabled="readOnly"
        @click="removeLanguage(index)"
      />
    </template>
  </NNTable>
</template>

<script>
import crfs from '@/api/crfs'
import NNTable from '@/components/tools/NNTable.vue'
import terms from '@/api/controlledTerminology/terms'
import { QuillEditor } from '@vueup/vue-quill'
import { useAccessGuard } from '@/composables/accessGuard'

export default {
  components: {
    NNTable,
    QuillEditor,
  },
  props: {
    editDescriptions: {
      type: Array,
      default: null,
    },
    readOnly: {
      type: Boolean,
      default: false,
    },
  },
  emits: ['setDesc'],
  setup() {
    return {
      ...useAccessGuard(),
    }
  },
  data() {
    return {
      desc: [],
      languages: [],
      headers: [
        { title: this.$t('CRFForms.language'), key: 'language', width: '10%' },
        {
          title: this.$t('CRFForms.displayed_text'),
          key: 'name',
          width: '15%',
        },
        { title: this.$t('CRFForms.description'), key: 'desc' },
        { title: this.$t('CRFForms.impl_notes'), key: 'notes' },
        { title: this.$t('CRFForms.compl_instructions'), key: 'inst' },
        { title: '', key: 'delete' },
      ],
      descriptionUids: [],
      customToolbar: [
        ['bold', 'italic', 'underline'],
        [{ script: 'sub' }, { script: 'super' }],
        [{ list: 'ordered' }, { list: 'bullet' }],
      ],
      descriptions: [],
      descKey: 0,
      quillOptions: {
        readOnly: true,
      },
    }
  },
  watch: {
    desc() {
      this.$emit('setDesc', this.desc)
    },
    editDescriptions() {
      if (this.editDescriptions) {
        this.desc = this.editDescriptions
      }
    },
  },
  mounted() {
    terms.getAttributesByCodelist('language').then((resp) => {
      this.languages = resp.data.items.filter(
        (el) => el.name_submission_value !== 'ENG'
      )
    })
    crfs.getDescriptions().then((resp) => {
      this.descriptions = resp.data.items
    })
    if (this.editDescriptions) {
      this.desc = this.editDescriptions
    }
  },
  methods: {
    createNewDescription(index) {
      this.desc[index].newDesc = true
      delete this.desc[index].sponsor_instruction
      delete this.desc[index].instruction
      delete this.desc[index].description
      delete this.desc[index].uid
      this.descKey += 1
    },
    addExistingDescription(item, index) {
      if (item.name) {
        this.desc[index].sponsor_instruction = item.name.sponsor_instruction
        this.desc[index].instruction = item.name.instruction
        this.desc[index].description = item.name.description
        this.desc[index].uid = item.name.uid
        this.desc[index].name = item.name.name
      }
      this.descKey += 1
    },
    addLanguage() {
      this.desc.push({ language: '' })
    },
    removeLanguage(index) {
      this.desc.splice(index, 1)
    },
  },
}
</script>
