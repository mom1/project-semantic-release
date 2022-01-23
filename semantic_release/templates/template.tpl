{{# previous_version }}
  {{# compare_url }}
    # [{{next_release.git_tag}}]({{compare_url}}) ({{# datetime }}%Y-%m-%d{{/datetime}})
  {{/ compare_url }}
  {{^ compare_url }}
    # {{next_release.git_tag}} ({{# datetime }}%Y-%m-%d{{/datetime}})
  {{/ compare_url }}
{{/ previous_version }}

{{# commits}}
*{{# scope}} **{{scope}}:**{{/scope}} {{subject}} [`{{commit.short}}`]({{# get_hash_link}}{{commit.long}}{{/get_hash_link}})
{{#body}}
{{{body}}}
{{/body}}
{{/commits}}
