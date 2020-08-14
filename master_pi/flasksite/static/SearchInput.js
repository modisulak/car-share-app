function _extends() { _extends = Object.assign || function (target) { for (var i = 1; i < arguments.length; i++) { var source = arguments[i]; for (var key in source) { if (Object.prototype.hasOwnProperty.call(source, key)) { target[key] = source[key]; } } } return target; }; return _extends.apply(this, arguments); }

// credit to https://medium.com/better-programming/
// learn-to-create-your-own-usefetch-react-hook-9cc31b038e53
// credit to https://react-select.com/home
const searchParams = new URL(document.location).searchParams;

const useFetch = (url, options) => {
  const [response, setResponse] = React.useState(null);
  const [error, setError] = React.useState(null);
  const [loading, setLoading] = React.useState(false);
  React.useEffect(() => {
    const abortController = new AbortController();
    const signal = abortController.signal;

    const doFetch = async () => {
      setLoading(true);

      try {
        const res = await fetch(url, options);
        const json = await res.json();

        if (!res.ok) {
          throw json;
        }

        if (!signal.aborted) {
          setResponse(json);
        }
      } catch (e) {
        if (!signal.aborted) {
          setError(e);
        }
      } finally {
        if (!signal.aborted) {
          setLoading(false);
        }
      }
    };

    doFetch();
    return () => {
      abortController.abort();
    };
  }, []);
  return {
    response,
    error,
    loading
  };
};

const SpeechRecogContext = React.createContext();

function Microphone(props) {
  return /*#__PURE__*/React.createElement("svg", _extends({
    width: "1em",
    height: "1em",
    viewBox: "0 0 16 16",
    fill: "currentColor"
  }, props), /*#__PURE__*/React.createElement("path", {
    d: "M5 3a3 3 0 016 0v5a3 3 0 01-6 0V3z"
  }), /*#__PURE__*/React.createElement("path", {
    fillRule: "evenodd",
    d: "M3.5 6.5A.5.5 0 014 7v1a4 4 0 008 0V7a.5.5 0 011 0v1a5 5 0 01-4.5 4.975V15h3a.5.5 0 010 1h-7a.5.5 0 010-1h3v-2.025A5 5 0 013 8V7a.5.5 0 01.5-.5z"
  }));
}

function VoiceSearchQuery({
  setResult
}) {
  const {
    response,
    loading,
    error
  } = useFetch("/api/voice", {
    method: "GET",
    credentials: "same-origin",
    headers: {
      "Content-Type": "application/json"
    },
    redirect: "manual"
  });
  React.useEffect(() => {
    if (response) {
      setResult(response);
    } else if (error) {
      alert(error);
    }
  }, [response, error]);
  return /*#__PURE__*/React.createElement(React.Fragment, null, loading && /*#__PURE__*/React.createElement("div", {
    class: "blob"
  }), error && /*#__PURE__*/React.createElement("button", {
    class: "label-danger disabled btn"
  }, "!"));
}

function VoiceSearch({
  value,
  setResult
}) {
  const [searching, setSearching] = React.useState(false);
  const [result, setSearchResult] = React.useState(null);
  React.useEffect(() => {
    if (result) {
      let new_value = {
        label: result.message,
        value: result.message
      };
      if (Array.isArray(value)) new_value = [...value, new_value];
      setResult(new_value);
      setSearching(false);
    }
  }, [result]);
  return /*#__PURE__*/React.createElement("div", {
    className: "input-group-append"
  }, searching ? /*#__PURE__*/React.createElement("span", {
    className: "input-group-text"
  }, /*#__PURE__*/React.createElement(VoiceSearchQuery, {
    setResult: e => setSearchResult(e)
  })) : /*#__PURE__*/React.createElement("button", {
    className: !searching && "btn btn-outline-secondary",
    type: "button",
    onClick: () => setSearching(true)
  }, /*#__PURE__*/React.createElement(Microphone, null)));
}

function SelectInputMap({
  checkboxes,
  selectValues,
  selectOptions,
  setSelectValues
}) {
  const speechRecogEnabled = React.useContext(SpeechRecogContext);
  return Object.entries(selectOptions).map(([key, options]) => {
    const checkbox = checkboxes[key];

    if (checkbox == undefined) {
      debugger;
    }

    const isSingle = checkbox.single;
    let value = selectValues[key];

    if (isSingle) {
      value = value[0];
    }

    return checkbox.enabled && /*#__PURE__*/React.createElement("div", {
      className: "input-group input-group-sm mb-3",
      key: key
    }, /*#__PURE__*/React.createElement("div", {
      className: "input-group-prepend noselect"
    }, /*#__PURE__*/React.createElement("span", {
      className: "input-group-text noselect"
    }, checkbox.label)), /*#__PURE__*/React.createElement(Select, {
      isMulti: !isSingle,
      name: key,
      options: options,
      value: value,
      onChange: e => setSelectValues({ ...selectValues,
        [key]: e
      }),
      className: "basic-multi-select form-control",
      classNamePrefix: "select"
    }), checkbox.voiceSearch && speechRecogEnabled && /*#__PURE__*/React.createElement(VoiceSearch, {
      value: value,
      setResult: e => setSelectValues({ ...selectValues,
        [key]: e
      })
    }));
  });
}

function FieldEnable({
  name,
  label,
  value,
  callback
}) {
  return /*#__PURE__*/React.createElement("div", {
    className: "custom-control custom-checkbox custom-control-inline noselect",
    onClick: callback
  }, /*#__PURE__*/React.createElement("input", {
    name: name,
    type: "checkbox",
    className: "custom-control-input m-2 noselect",
    checked: value,
    onChange: callback
  }), /*#__PURE__*/React.createElement("label", {
    className: "custom-control-label noselect"
  }, label));
}

function FilterBy({
  checkboxes,
  setCheckboxes
}) {
  return /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("span", {
    className: "mr-3 mb-5"
  }, /*#__PURE__*/React.createElement("strong", null, "Filter By:")), /*#__PURE__*/React.createElement("div", {
    className: "form-group"
  }, Object.entries(checkboxes).map(([k, v]) => !v.hide && /*#__PURE__*/React.createElement(FieldEnable, {
    key: k,
    name: k,
    label: v.label,
    value: v.enabled,
    callback: () => setCheckboxes({ ...checkboxes,
      [k]: { ...v,
        enabled: !v.enabled
      }
    })
  }))));
}

function CheckSpeechRecogStatus({
  setResult
}) {
  const {
    response,
    error
  } = useFetch("api/voice/ping", {
    method: "GET",
    credentials: "same-origin",
    headers: {
      "Content-Type": "application/text"
    },
    redirect: "manual"
  });
  React.useEffect(() => {
    if (response) {
      setResult(true);
    }

    if (error) {
      setResult(false);
    }
  }, [response, error]);
  return /*#__PURE__*/React.createElement(React.Fragment, null);
}

function SelectSearch({
  availableFields,
  fieldOptions,
  selectValueDefaults,
  selectOptionsURI
}) {
  const [checkboxes, setCheckboxes] = React.useState(availableFields);
  React.useEffect(() => {
    Object.keys(checkboxes).forEach(k => {
      const check = searchParams.get(k);

      if (check) {
        checkboxes[k].enabled = check;
      }
    });
  }, []);
  const [selectOptions, setSelectOptions] = React.useState(fieldOptions);
  const fieldValues = {};

  for (key of Object.keys(fieldOptions)) {
    fieldValues[key] = [];
  }

  const [selectValues, setSelectValues] = React.useState(fieldValues); // apply url search params to SelectInputs

  React.useEffect(() => {
    const newSelectValues = { ...selectValues
    };
    const newSelectOptions = { ...selectOptions
    };
    Object.entries(selectOptions).forEach(([k, values]) => {
      const paramOptions = searchParams.getAll(k).filter(p => p !== "" && p !== "on");

      if (paramOptions.length) {
        const fullItem = values.filter(v => paramOptions.includes(v.value));

        if (fullItem.length) {
          newSelectValues[k].push(...fullItem);
        } else {
          const temp = paramOptions.map(v => ({
            value: v,
            label: v
          }));
          newSelectValues[k].push(...temp);
          newSelectOptions[k].push(...temp);
        }
      } else if (selectValueDefaults[k] !== undefined) {
        newSelectValues[k].push(...selectValueDefaults[k]);
      }
    });
    setSelectValues(newSelectValues);
    setSelectOptions(newSelectOptions);
  }, []);
  const {
    response,
    loading,
    error
  } = useFetch(selectOptionsURI, {
    method: "GET",
    credentials: "same-origin",
    headers: {
      "Content-Type": "application/json"
    },
    redirect: "manual"
  }); // apply response to SelectInputs

  React.useEffect(() => {
    if (response) {
      newSelectOptions = { ...selectOptions
      };
      Object.entries(response).forEach(([k, v]) => {
        const map = v.map(e => ({
          value: e[k],
          label: e[k]
        }));
        map.sort((a, b) => {
          return String(a.value).localeCompare(String(b.value));
        });
        newSelectOptions[k] = map;
      });
      setSelectOptions(newSelectOptions);
    }
  }, [response]);

  if (error) {
    console.log(error);
  }

  const [speechRecogStatus, setSpeechRecogStatus] = React.useState(false);
  return /*#__PURE__*/React.createElement(SpeechRecogContext.Provider, {
    value: speechRecogStatus
  }, /*#__PURE__*/React.createElement("fieldset", {
    className: "form-group col-md-6 offset-md-3"
  }, /*#__PURE__*/React.createElement(CheckSpeechRecogStatus, {
    setResult: e => setSpeechRecogStatus(e)
  }), /*#__PURE__*/React.createElement(FilterBy, {
    checkboxes,
    setCheckboxes
  }), loading && /*#__PURE__*/React.createElement("div", {
    className: "progress m-3",
    style: {
      height: "3px"
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "progress-bar progress-bar-striped progress-bar-animated",
    role: "progressbar",
    style: {
      width: "90%"
    }
  })), /*#__PURE__*/React.createElement(SelectInputMap, {
    checkboxes,
    selectValues,
    selectOptions,
    setSelectValues
  }), /*#__PURE__*/React.createElement("input", {
    className: "btn btn-link btn-primary btn-block btn",
    name: "submit",
    type: "submit",
    value: "Search"
  }), error && /*#__PURE__*/React.createElement("p", null, "Something went wrong...")));
}

userAvailableFields = {
  id: {
    label: "User ID",
    enabled: false
  },
  username: {
    label: "Username",
    enabled: false
  },
  firstname: {
    label: "First Name",
    enabled: false
  },
  lastname: {
    label: "Last Name",
    enabled: false
  },
  userType: {
    label: "User Type",
    enabled: false
  },
  email: {
    label: "Email",
    enabled: false
  },
  order_by: {
    label: "Order By",
    enabled: false,
    hide: true,
    single: true
  }
};
userFieldOptions = {
  id: [],
  username: [],
  firstname: [],
  lastname: [],
  userType: [],
  email: [],
  order_by: []
};
userSelectValueDefaults = {};
userSelectOptionsURI = "/api/users?search_data=all";

function UserSelectSearch() {
  return /*#__PURE__*/React.createElement(SelectSearch, {
    availableFields: userAvailableFields,
    fieldOptions: userFieldOptions,
    selectValueDefaults: userSelectValueDefaults,
    selectOptionsURI: userSelectOptionsURI
  });
}

carAvailableFields = {
  id: {
    label: "Car ID",
    enabled: false,
    voiceSearch: true
  },
  make: {
    label: "Make",
    enabled: false,
    voiceSearch: true
  },
  body_type: {
    label: "Body Type",
    enabled: false,
    voiceSearch: true
  },
  colour: {
    label: "Colour",
    enabled: false,
    voiceSearch: true
  },
  seats: {
    label: "Seats",
    enabled: false,
    voiceSearch: true
  },
  is_active: {
    label: "Available Only",
    enabled: false
  },
  order_by: {
    label: "Order By",
    enabled: true,
    hide: true,
    single: true
  }
};
carFieldOptions = {
  id: [],
  make: [],
  body_type: [],
  colour: [],
  seats: [],
  order_by: [{
    label: "Price: Ascending",
    value: "price_asc"
  }, {
    label: "Price: Descending",
    value: "price_desc"
  }]
};
carSelectValueDefaults = {
  order_by: [{
    label: "Price: Descending",
    value: "price_desc"
  }]
};
carSelectOptionsURI = "/api/cars?search_data=all";

function CarSelectSearch() {
  return /*#__PURE__*/React.createElement(SelectSearch, {
    availableFields: carAvailableFields,
    fieldOptions: carFieldOptions,
    selectValueDefaults: carSelectValueDefaults,
    selectOptionsURI: carSelectOptionsURI
  });
}

userReactSelect = document.getElementById("user-react-select");
if (userReactSelect) ReactDOM.render( /*#__PURE__*/React.createElement(UserSelectSearch, null), userReactSelect);
carReactSelect = document.getElementById("car-react-select");
if (carReactSelect) ReactDOM.render( /*#__PURE__*/React.createElement(CarSelectSearch, null), carReactSelect);

//# sourceMappingURL=SearchInput.js.map