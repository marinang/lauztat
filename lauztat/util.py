from contextlib import ExitStack


def integrate_pdf(model, bounds, params):

    if "zfit" in str(model.__class__):
        import zfit

        def integrate(models, bounds):
            ret = zfit.run(models.integrate(bounds))
            return ret
    else:
        def integrate(models, bounds):
            return NotImplemented

    deps = list(model.get_dependents())

    with ExitStack() as stack:
        for p in deps:
            value = params[p]["value"]
            stack.enter_context(p.set_value(value))
        ret = integrate(model, bounds)

    return ret


def eval_pdf(model, x, params):
    if "zfit" in str(model.__class__):
        import zfit

        def eval_(model, x):
            ret = zfit.run(model.pdf(x))
            return ret
    else:
        def eval_(model, x):
            return NotImplemented

    deps = list(model.get_dependents())

    with ExitStack() as stack:
        for p in deps:
            value = params[p]["value"]
            stack.enter_context(p.set_value(value))
        ret = eval_(model, x)

    return ret


def convert_dataset(dataset, array, weights=None):
    """
    dataset: only used to get the class in which array/weights will be
    converted.
    """

    if "zfit" in str(dataset.__class__):
        import zfit
        obs = dataset.obs
        converter = zfit.data.Data.from_numpy
        ret = converter(obs=obs, array=array, weights=weights)
        return ret
    else:
        raise NotImplementedError
