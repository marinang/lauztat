from iminuit import Minuit
from .loss import UnbinnedNLL
from collections import OrderedDict
import copy


class MinuitMinimizer(object):

    def __init__(self):
        self._minuit_minimizer = None

    def minimize(self, loss, params=None, **kwargs):

        if not isinstance(loss, UnbinnedNLL):
            msg = "Incorrect type for 'loss'. 'UnbinnedNLL',"
            msg += " 'ExtendedUnbinnedNLL' expected."
            raise TypeError(msg)

        lossfunction, floatings = loss.loss_function(params)

        for f in floatings:
            pars = f.tominuit()
            kwargs.update(pars)

        minuit = Minuit(lossfunction, errordef=loss.errordef, **kwargs)
        self._minuit_minimizer = minuit

        result = minuit.migrad()

        params_result = [p_dict for p_dict in result[1]]
        for f, p in zip(floatings, params_result):
            f.set_value(p["value"])

        info = {'n_eval': result[0]['nfcn'], 'original': result[0]}
        edm = result[0]['edm']
        fmin = result[0]['fval']
        status = -999
        converged = result[0]['is_valid']
        params = OrderedDict((p, res['value'])
                             for p, res in zip(floatings, params_result))
        result = FitResult(params=params, edm=edm, fmin=fmin, info=info,
                           loss=loss,
                           status=status, converged=converged,
                           minimizer=self.copy())

        return result

    def copy(self):
        return copy.copy(self)


def _hesse_minuit(result, params, sigma=1.0):
    if sigma != 1.0:
        raise ValueError("sigma other then 1 is not valid for minuit hesse.")
    fitresult = result
    minimizer = fitresult.minimizer
    from zfit.minimizers.minimizer_minuit import MinuitMinimizer
    if not isinstance(minimizer, MinuitMinimizer):
        msg = "Cannot perform hesse error calculation 'minuit' with a"
        msg += " different minimizer then `MinuitMinimizer`."
        raise TypeError(msg)

    params_name = OrderedDict((param.name, param) for param in params)
    result_hesse = minimizer._minuit_minimizer.hesse()
    result_hesse = OrderedDict((res['name'], res) for res in result_hesse)

    result = OrderedDict((params_name[p_name], {'error': res['error']})
                         for p_name, res in result_hesse.items()
                         if p_name in params_name)
    return result


def _minos_minuit(result, params, sigma=1.0):
    fitresult = result
    minimizer = fitresult.minimizer
    from zfit.minimizers.minimizer_minuit import MinuitMinimizer
    if not isinstance(minimizer, MinuitMinimizer):
        msg = "Cannot perform error calculation 'minos_minuit' with a"
        msg += "different minimizer then `MinuitMinimizer`."
        raise TypeError(msg)

    result = [minimizer._minuit_minimizer.minos(var=p.name, sigma=sigma)
              for p in params][-1]  # returns every var
    result = OrderedDict((p, result[p.name]) for p in params)
    return result


class FitResult(object):

    _default_hesse = 'minuit_hesse'
    _hesse_methods = {'minuit_hesse': _hesse_minuit}
    _default_error = 'minuit_minos'
    _error_methods = {"minuit_minos": _minos_minuit}

    def __init__(self, params, edm, fmin, status, converged, info, loss,
                 minimizer):

        self._status = status
        self._converged = converged
        self._params = self._input_convert_params(params)
        self._edm = edm
        self._fmin = fmin
        self._info = info
        self._loss = loss
        self._minimizer = minimizer

    def _input_convert_params(self, params):
        params = OrderedDict((p, {'value': v}) for p, v in params.items())
        return params

    def _get_uncached_params(self, params, method_name):
        params_uncached = [p for p in params if self.params[p].get(method_name)
                           is None]
        return params_uncached

    @property
    def params(self):
        return self._params

    @property
    def edm(self):
        """The estimated distance to the minimum.
        Returns:
            numeric
        """
        edm = self._edm
        return edm

    @property
    def minimizer(self):
        return self._minimizer

    @property
    def loss(self):
        return self._loss

    @property
    def fmin(self):
        """Function value at the minimum.
        Returns:
            numeric
        """
        fmin = self._fmin
        return fmin

    @property
    def status(self):
        status = self._status
        return status

    @property
    def info(self):
        return self._info

    @property
    def converged(self):
        return self._converged

    def _input_check_params(self, params):
        params = list(self.params.keys())
        return params

    def hesse(self, params=None, method='minuit_hesse', error_name=None):

        if error_name is None:
            if not isinstance(method, str):
                msg = "Need to specify `error_name` or use a string as"
                msg += " `method`"
                raise ValueError(msg)
            error_name = method
        params = self._input_check_params(params)
        uncached_params = self._get_uncached_params(params=params,
                                                    method_name=error_name)
        if uncached_params:
            error_dict = self._hesse(params=uncached_params, method=method)
            self._cache_errors(error_name=error_name, errors=error_dict)
        all_errors = OrderedDict((p, self.params[p][error_name])
                                 for p in params)
        return all_errors

    def _cache_errors(self, error_name, errors):
        for param, errors in errors.items():
            self.params[param][error_name] = errors

    def _hesse(self, params, method):
        if not callable(method):
            try:
                method = self._hesse_methods[method]
            except KeyError:
                msg = "The following method is not a valid, implemented"
                msg += "method: {}"
                raise KeyError(msg.format(method))
        return method(result=self, params=params)

    def error(self, params=None, method='minuit_minos', error_name=None,
              sigma=1.0):

        if error_name is None:
            if not isinstance(method, str):
                msg = "Need to specify `error_name` or use a string as"
                msg += " `method`"
                raise ValueError(msg)
            error_name = method
        params = self._input_check_params(params)
        uncached_params = self._get_uncached_params(params=params,
                                                    method_name=error_name)

        if uncached_params:
            error_dict = self._error(params=uncached_params, method=method,
                                     sigma=sigma)
            self._cache_errors(error_name=error_name, errors=error_dict)
        all_errors = OrderedDict((p, self.params[p][error_name])
                                 for p in params)
        return all_errors

    def _error(self, params, method, sigma):
        if not callable(method):
            try:
                method = self._error_methods[method]
            except KeyError:
                msg = "The following method is not a valid,"
                msg += " implemented method: {}"
                raise KeyError(msg.format(method))
        return method(result=self, params=params, sigma=sigma)


class MinimizerWrapper(object):

    def __init__(self, lossfunction, **kwargs):

        if not isinstance(lossfunction, (LossFunctionWrapper,
                                         SimultaneousFitWrapper)):
            raise ValueError("Loss function need to be wrapped under\
                             statnight.utils.LossFunctionWrapper.")
        for v in lossfunction.variables:
            pars = v.tominuit()
            kwargs.update(pars)

        minuit = Minuit(lossfunction, errordef=0.5, **kwargs)

        self._minuit = minuit
        self._nfreeparameters = len(lossfunction.freeparameters)

    def minimize(self):
        self._minuit.migrad()

    @property
    def values(self):
        return dict(self._minuit.values)

    @property
    def errors(self):
        return dict(self._minuit.errors)

    @property
    def nfreeparameters(self):
        return self._nfreeparameters

    @property
    def result(self):
        return dict(values=self.values, errors=self.errors,
                    nfreeparameters=self.nfreeparameters)

    def profile(self, param, value):
        range = (value, -1.)
        prof = self._minuit.mnprofile(param, 1, range)
        if prof[1] > 0:
            print("WARNING! Large positive value for EDM for ", value)
        return prof[1]
