<template>
  <NNTable
    :headers="headers"
    :items="items"
    :items-length="total"
    hide-default-switches
    column-data-resource="projects"
    item-value="project_number"
    @filter="fetchProjects"
  >
    <template #actions="">
      <slot name="extraActions" />
      <v-btn
        size="small"
        color="primary"
        data-cy="add-project"
        :title="$t('ProjectForm.title')"
        icon="mdi-plus"
        @click.stop="showForm"
      />
    </template>
  </NNTable>
  <ProjectForm :open="showProjectForm" @close="closeForm" />
</template>

<script>
import NNTable from '@/components/tools/NNTable.vue'
import projects from '@/api/projects'
import ProjectForm from '@/components/library/ProjectForm.vue'
import filteringParameters from '@/utils/filteringParameters'

export default {
  components: {
    NNTable,
    ProjectForm,
  },
  data() {
    return {
      headers: [
        { title: this.$t('Projects.name'), key: 'name' },
        { title: this.$t('Projects.project_number'), key: 'project_number' },
        {
          title: this.$t('Projects.clinical_programme'),
          key: 'clinical_programme.name',
        },
        { title: this.$t('Projects.description'), key: 'description' },
      ],
      items: [],
      total: 0,
      filters: '',
      showProjectForm: false,
    }
  },
  methods: {
    fetchProjects(filters, options, filtersUpdated) {
      if (!filters && this.filters) {
        filters = this.filters
      }
      const params = filteringParameters.prepareParameters(
        options,
        filters,
        filtersUpdated
      )
      this.filters = filters
      projects.get(params).then((resp) => {
        this.items = resp.data.items
        this.total = resp.data.total
      })
    },
    showForm() {
      this.showProjectForm = true
    },
    closeForm() {
      this.showProjectForm = false
      this.fetchProjects()
    },
  },
}
</script>
