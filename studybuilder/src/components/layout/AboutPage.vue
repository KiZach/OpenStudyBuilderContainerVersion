<template>
  <v-card color="dfltBackground">
    <v-card-actions>
      <v-card-title class="dialog-about-title">
        {{ $t('About.title') }}
      </v-card-title>
      <v-spacer />
      <v-btn
        class="secondary-btn"
        color="white"
        variant="elevated"
        @click="$emit('close')"
      >
        {{ $t('_global.close') }}
      </v-btn>
    </v-card-actions>
    <v-card-text>
      <p>
        {{ $t('About.about_release_number') }}
        {{ $config.RELEASE_VERSION_NUMBER }}
      </p>
      <p>
        {{ $t('About.components_list') }} {{ $config.STUDYBUILDER_VERSION }}
      </p>
      <p>{{ $t('About.header') }}</p>
      <v-table>
        <thead>
          <tr>
            <th id="component">
              {{ $t('About.component') }}
            </th>
            <th id="description">
              {{ $t('About.description') }}
            </th>
            <th id="build_number">
              {{ $t('About.build_number') }}
            </th>
            <th id="license">
              {{ $t('About.license') }}
            </th>
            <th id="sbom">
              {{ $t('About.sbom') }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="component in sbComponents" :key="component.name">
            <td>{{ component.name }}</td>
            <td>{{ component.description }}</td>
            <td>{{ component.build_number }}</td>
            <td>
              <v-btn
                v-if="component.component"
                variant="text"
                @click="
                  showLicenseText(
                    component.component,
                    component.name,
                    'license'
                  )
                "
              >
                {{ $t('_global.view') }}
              </v-btn>
            </td>
            <td>
              <v-btn
                v-if="component.component"
                variant="text"
                @click="
                  showLicenseText(component.component, component.name, 'sbom')
                "
              >
                {{ $t('_global.view') }}
              </v-btn>
            </td>
          </tr>
        </tbody>
      </v-table>
    </v-card-text>
    <v-dialog v-model="showLicense" scrollable max-width="800">
      <AboutLicense
        :raw-markdown="licenseText"
        :title="licenseTitle"
        @close="showLicense = false"
      />
    </v-dialog>
  </v-card>
</template>

<script>
import AboutLicense from './AboutLicense.vue'
import axios from 'axios'
import system from '@/api/system'

export default {
  components: {
    AboutLicense,
  },
  emits: ['close'],
  data() {
    return {
      licenses: {},
      licenseText: null,
      licenseTitle: '',
      sboms: {},
      showLicense: false,
      sbComponents: [
        {
          name: this.$t('About.studybuilder'),
          description: this.$t('About.studybuilder_description'),
          build_number: this.$config.FRONTEND_BUILD_NUMBER,
          component: 'studybuilder',
        },
        {
          name: this.$t('About.documentation-portal'),
          description: this.$t('About.documentation-portal_description'),
          build_number: this.$config.DOCUMENTATION_PORTAL_BUILD_NUMBER,
          component: 'documentation-portal',
        },
        {
          name: this.$t('About.clinical-mdr-api'),
          description: this.$t('About.clinical-mdr-api_description'),
          build_number: this.$config.API_BUILD_NUMBER,
          component: 'clinical-mdr-api',
        },
        {
          name: this.$t('About.database'),
          description: this.$t('About.db_description'),
        },
        {
          name: this.$t('About.studybuilder-import'),
          description: this.$t('About.studybuilder-import_description'),
          build_number: this.$config.DATA_IMPORT_BUILD_NUMBER,
          component: 'studybuilder-import',
        },
        {
          name: this.$t('About.mdr-standards-import'),
          description: this.$t('About.mdr-standards-import_description'),
          build_number: this.$config.STANDARDS_IMPORT_BUILD_NUMBER,
          component: 'mdr-standards-import',
        },
        {
          name: this.$t('About.neo4j-mdr-db'),
          description: this.$t('About.neo4j-mdr-db_description'),
          build_number: this.$config.NEO4J_MDR_BUILD_NUMBER,
          component: 'neo4j-mdr-db',
        },
        {
          name: this.$t('About.studybuilder-export'),
          description: this.$t('About.studybuilder-export_description'),
          build_number: this.$config.STUDYBUILDER_EXPORT_BUILD_NUMBER,
          component: 'studybuilder-export',
        },
      ],
    }
  },
  mounted() {
    system.getInformation().then((response) => {
      this.sbComponents[3].build_number = response.data.db_version
    })
    this.fetchFiles()
  },
  methods: {
    async fetchFiles() {
      const components = [
        'studybuilder',
        'documentation-portal',
        'clinical-mdr-api',
        'studybuilder-import',
        'mdr-standards-import',
        'neo4j-mdr-db',
        'studybuilder-export',
      ]
      const url =
        process.env.NODE_ENV === 'development' ? '' : `https://${location.host}`
      for (const component of components) {
        const license = await axios.get(`${url}/LICENSE-${component}.md`)
        this.licenses[component] = license.data
        const sbom = await axios.get(`${url}/sbom-${component}.md`)
        this.sboms[component] = sbom.data
      }
    },
    showLicenseText(component, title, type) {
      this.licenseText =
        type === 'license' ? this.licenses[component] : this.sboms[component]
      this.showLicense = true
      this.licenseTitle = title
    },
  },
}
</script>
