{% for sig_name, sig_dict in signals.items() %}
generated_{{sig_name}} = np.array(0, dtype=np.{{sig_dict["dtype"]}})
{% endfor %}
