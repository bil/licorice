{% for sig_name, sig_dict in out_signals.items() %}
if generated_{{sig_name}} < 100:
    generated_{{sig_name}} = np.add(
        generated_{{sig_name}}, 1, dtype=np.{{sig_dict["dtype"]}}
    )
else:
    generated_{{sig_name}} = np.array(1, dtype=np.{{sig_dict["dtype"]}})

# write to outputs
    {% if "vector" in sig_name %}
{{sig_name}}[:] = np.array([generated_{{sig_name}}] * {{sig_dict["shape"]}})
    {% else %}
{{sig_name}}[:] = generated_{{sig_name}}
    {% endif %}
{% endfor %}
