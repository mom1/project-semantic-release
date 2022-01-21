const Configuration = {
    extends: ['@commitlint/config-conventional'],
    parserPreset: 'conventional-changelog-conventionalcommits',
    rules: {
        'subject-case': [
            2,
            'never',
            ['start-case', 'pascal-case', 'upper-case'],
        ],
    },
    ignores: [(commit) => commit === ''],
    defaultIgnores: true,
};

module.exports = Configuration;
