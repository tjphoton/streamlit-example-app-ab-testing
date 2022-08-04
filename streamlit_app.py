import streamlit as st
import pandas as pd
import numpy as np
import scipy.stats as stats
from scipy.stats import norm
import altair as alt
import matplotlib.pyplot as plt


st.set_page_config(
    page_title="Significance Testing App", page_icon="📊", initial_sidebar_state="expanded"
)


def conversion_rate(conversions, visitors):
    return (conversions / visitors) * 100


def lift(cra, crb):
    return (crb - cra)


def std_err(cr, visitors):
    return np.sqrt((cr / 100 * (1 - cr / 100)) / visitors)


def std_err_diff(sea, seb):
    return np.sqrt(sea ** 2 + seb ** 2)


def z_score(conversions_a, conversions_b, visitors_a, visitors_b):
    cr = (conversions_a + conversions_b) / (visitors_a + visitors_b)
    cra = conversions_a / visitors_a
    crb = conversions_b / visitors_b
    return (crb - cra)/np.sqrt(cr*(1-cr)*(1/visitors_a+1/visitors_b))

def p_value(z, hypothesis):
    if hypothesis == "One-sided":
        if z < 0:
            p_value = 1 - norm().sf(z)
        if z >= 0:
            p_value = norm().sf(z)
    else:
        if z < 0:
            p_value = (1 - norm().sf(z)) * 2
        if z >= 0:
            p_value = norm().sf(z) * 2
    return p_value

def significance(alpha, p):
    return "YES" if p < alpha else "NO"


def plot_chart(df):
    """
    Diplays a bar chart of conversion rates of A/B test groups,
    with the y-axis denoting the conversion rates.
    """
    chart = (
        alt.Chart(df)
        .mark_bar(color="#61b33b")
        .encode(
            x=alt.X("Group:O", axis=alt.Axis(labelAngle=0)),
            y=alt.Y("Conversion:Q", title="Conversion rate (%)"),
            opacity="Group:O",
        )
        .properties(width=500, height=500)
    )

    # Place conversion rate as text above each bar
    chart_text = chart.mark_text(
        align="center", baseline="middle", dy=-10, color="black"
    ).encode(text=alt.Text("Conversion:Q", format=",.3g"))

    return st.altair_chart((chart + chart_text).interactive())


def style_negative(v, props=""):
    """Helper function to color text in a DataFrame if it is negative.
    >>> df.style.applymap(style_negative, props="color:red;")
    """
    return props if v < 0 else None


def style_p_value(v, props=""):
    """Helper function to color p-value in DataFrame. If p-value is
    statististically significant, text is colored green; else red.
    Parameters
    ----------
    v: float
        The text (value) in a DataFrame to color
    props: str
        A string with a CSS attribute-value pair. E.g "color:green;"
        See: https://pandas.pydata.org/pandas-docs/stable/user_guide/style.html
    Returns
    -------
    A styled DataFrame with negative values colored in red.
    Example
    -------
    >>> df.style.apply(style_p_value, props="color:red;", axis=1, subset=["p-value"])
    """
    return np.where(v < st.session_state.alpha, "color:green;", props)


def calculate_significance(
    conversions_a, conversions_b, visitors_a, visitors_b, hypothesis, alpha
):
    st.session_state.cra = conversion_rate(int(conversions_a), int(visitors_a))
    st.session_state.crb = conversion_rate(int(conversions_b), int(visitors_b))
    st.session_state.diff = lift(st.session_state.cra, st.session_state.crb)
    st.session_state.sea = std_err(st.session_state.cra, float(visitors_a))
    st.session_state.seb = std_err(st.session_state.crb, float(visitors_b))
    st.session_state.sed = std_err_diff(st.session_state.sea, st.session_state.seb)
    st.session_state.z = z_score(
        conversions_a, conversions_b, visitors_a, visitors_b
    )
    st.session_state.p = p_value(st.session_state.z, st.session_state.hypothesis)
    st.session_state.significant = significance(
        st.session_state.alpha, st.session_state.p
    )

st.write(
    """
    ## Significance Calculation Tool
    """
)
st.image("versai.png", width=120)
st.write("")
st.write("")

st.markdown("### Type in your data (or use the default sample data)")
#st.write("Type in your data to see whether the difference between two groups is significant")

col1, col2 = st.columns(2)

with col1:
    st.markdown("##### Group A")
    Pop_A = st.number_input('population count', value = 228)
    Evt_A = st.number_input('event count', value = 23)

with col2:
    st.markdown("##### Group B")
    Pop_B = st.number_input('population count', value=254)
    Evt_B = st.number_input('event count', value = 41)

st.markdown("### Adjust test parameters")

with st.form(key="my_form"):
    col1, col2, col3 = st.columns(3)

    with col1:
        st.radio(
            "Hypothesis type",
            options=["Two-sided", "One-sided"],
            index=0,
            key="hypothesis",
            help="Use a two-tailed test when you want to test the difference between two groups. "
                 "Only use one-tailed test if you have a specific prediction about the direction of the difference, "
                 "because it has more statistical power than a two-tailed test at the same significance (alpha) level. "
                 "When in doubt, it is almost always more appropriate to two-tailed test. "
        )

    with col2:
        st.slider(
            "Significance level (α)",
            min_value=0.01,
            max_value=0.20,
            value=0.05,
            step=0.01,
            key="alpha",
            help=" The probability of mistakenly rejecting the null hypothesis, if the null hypothesis is true. This is also called false positive and type I error. ",
        )
    with col3:
        submit_button = st.form_submit_button(label="Submit")

# Obtain the metrics to display
calculate_significance(
    Evt_A,
    Evt_B,
    Pop_A,
    Pop_B,
    st.session_state.hypothesis,
    st.session_state.alpha,
)

st.markdown("### Result")

# Use st.metric to diplay difference in conversion rates
mcol1, mcol2 = st.columns(2)

with mcol1:
    st.metric(
        "Difference",
        value=f"{(st.session_state.crb - st.session_state.cra):.3g}%",
    )
# Display whether or not A/B test result is statistically significant
with mcol2:
    st.metric("Significant?", value=st.session_state.significant)

st.markdown("### Result Explanation")

mcol1, mcol2 = st.columns(2)

with mcol1:
    table = pd.DataFrame(
        {
            "Event": [Evt_A, Evt_B],
            "Population": [Pop_A, Pop_B],
            "% events": [st.session_state.cra, st.session_state.crb],
        },
        index=pd.Index(["Group A", "Group B"]),
    )

    # Format "% Converted" column values to 3 decimal places
    table1 = st.write(table.style.format(formatter={("% events"): "{:.3g}%"}))

    metrics = pd.DataFrame(
        {
            "diff": [st.session_state.diff],
            "z-score": [st.session_state.z],
            "p-value": [st.session_state.p],
        },
        index=pd.Index(["Metrics"]),
    )

    # Color negative values red; color significant p-value green and not significant red
    table2 = st.write(
        metrics.style.format(
            formatter={("p-value", "z-score"): "{:.3g}", ("diff"): "{:.3g}%"}
        )
            # .applymap(style_negative, props="color:red;")
            .apply(style_p_value, props="color:red;", axis=1, subset=["p-value"])
    )

with mcol2:
    labels = ['Group A', 'Group B']
    x_pos = np.arange(len(labels))
    cra = [st.session_state.cra, st.session_state.crb]
    if st.session_state.hypothesis  == "One-sided":
        z = stats.norm.ppf(1-st.session_state.alpha)
    else:
        z = stats.norm.ppf(1-st.session_state.alpha/2)
    error = [st.session_state.sea*100*z, st.session_state.seb*100*z]

    fig, ax = plt.subplots()
    ax.bar(x_pos,
           cra,
           yerr=error,
           align='center',
           alpha=0.5,
           ecolor='black',
           capsize=10)

    ax.set_ylabel("event %")
    ax.yaxis.grid(True)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(labels)
    ax.set_title(f"Event % at {(1-st.session_state.alpha)*100}% Confidence Level")

    st.pyplot(fig)