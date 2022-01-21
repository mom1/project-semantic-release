{{# previous_version }}
  {{# compare_url }}
    # [{{next_release.git_tag}}]({{compare_url}}) ({{# datetime }}%Y-%m-%d{{/datetime}})
  {{/ compare_url }}
  {{^ compare_url }}
    # {{next_release.git_tag}} ({{# datetime }}%Y-%m-%d{{/datetime}})
  {{/ compare_url }}
{{/ previous_version }}

{{# commits}}
*{{# scope}} **{{scope}}:**{{/scope}} {{subject}} [`{{commit.short}}`](https://github.com/{{owner}}/{{repo_name}}/commit/{{commit.short}})
{{#body}}
{{{body}}}
{{/body}}
{{/commits}}
