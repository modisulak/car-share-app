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
    return { response, error, loading };
};

const SpeechRecogContext = React.createContext();

function Microphone(props) {
    return (
        <svg
            width="1em"
            height="1em"
            viewBox="0 0 16 16"
            fill="currentColor"
            {...props}
        >
            <path d="M5 3a3 3 0 016 0v5a3 3 0 01-6 0V3z" />
            <path
                fillRule="evenodd"
                d="M3.5 6.5A.5.5 0 014 7v1a4 4 0 008 0V7a.5.5 0 011 0v1a5 5 0 01-4.5 4.975V15h3a.5.5 0 010 1h-7a.5.5 0 010-1h3v-2.025A5 5 0 013 8V7a.5.5 0 01.5-.5z"
            />
        </svg>
    );
}

function VoiceSearchQuery({ setResult }) {
    const { response, loading, error } = useFetch("/api/voice", {
        method: "GET",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        redirect: "manual",
    });
    React.useEffect(() => {
        if (response) {
            setResult(response);
        } else if (error) {
            alert(error);
        }
    }, [response, error]);
    return (
        <React.Fragment>
            {loading && <div class="blob"></div>}
            {error && <button class="label-danger disabled btn">!</button>}
        </React.Fragment>
    );
}

function VoiceSearch({ value, setResult }) {
    const [searching, setSearching] = React.useState(false);
    const [result, setSearchResult] = React.useState(null);
    React.useEffect(() => {
        if (result) {
            let new_value = { label: result.message, value: result.message };
            if (Array.isArray(value)) new_value = [...value, new_value];
            setResult(new_value);
            setSearching(false);
        }
    }, [result]);
    return (
        <div className="input-group-append">
            {searching ? (
                <span className="input-group-text">
                    <VoiceSearchQuery setResult={(e) => setSearchResult(e)} />
                </span>
            ) : (
                <button
                    className={!searching && "btn btn-outline-secondary"}
                    type="button"
                    onClick={() => setSearching(true)}
                >
                    <Microphone />
                </button>
            )}
        </div>
    );
}

function SelectInputMap({
    checkboxes,
    selectValues,
    selectOptions,
    setSelectValues,
}) {
    const speechRecogEnabled = React.useContext(SpeechRecogContext);
    return Object.entries(selectOptions).map(([key, options]) => {
        const checkbox = checkboxes[key];
        const isSingle = checkbox.single;
        let value = selectValues[key];
        if (isSingle) {
            value = value[0];
        }
        return (
            checkbox.enabled && (
                <div className="input-group input-group-sm mb-3" key={key}>
                    <div className="input-group-prepend noselect">
                        <span className="input-group-text noselect">
                            {checkbox.label}
                        </span>
                    </div>
                    <Select
                        isMulti={!isSingle}
                        name={key}
                        options={options}
                        value={value}
                        onChange={(e) =>
                            setSelectValues({
                                ...selectValues,
                                [key]: e,
                            })
                        }
                        className="basic-multi-select form-control"
                        classNamePrefix="select"
                    />
                    {checkbox.voiceSearch && speechRecogEnabled && (
                        <VoiceSearch
                            value={value}
                            setResult={(e) =>
                                setSelectValues({
                                    ...selectValues,
                                    [key]: e,
                                })
                            }
                        />
                    )}
                </div>
            )
        );
    });
}

function FieldEnable({ name, label, value, callback }) {
    return (
        <div
            className="custom-control custom-checkbox custom-control-inline noselect"
            onClick={callback}
        >
            <input
                name={name}
                type="checkbox"
                className="custom-control-input m-2 noselect"
                checked={value}
                onChange={callback}
            />
            <label className="custom-control-label noselect">{label}</label>
        </div>
    );
}

function FilterBy({ checkboxes, setCheckboxes }) {
    return (
        <React.Fragment>
            <span className="mr-3 mb-5">
                <strong>Filter By:</strong>
            </span>
            <div className="form-group">
                {Object.entries(checkboxes).map(
                    ([k, v]) =>
                        !v.hide && (
                            <FieldEnable
                                key={k}
                                name={k}
                                label={v.label}
                                value={v.enabled}
                                callback={() =>
                                    setCheckboxes({
                                        ...checkboxes,
                                        [k]: { ...v, enabled: !v.enabled },
                                    })
                                }
                            />
                        ),
                )}
            </div>
        </React.Fragment>
    );
}

function CheckSpeechRecogStatus({ setResult }) {
    const { response, error } = useFetch("api/voice/ping", {
        method: "GET",
        credentials: "same-origin",
        headers: { "Content-Type": "application/text" },
        redirect: "manual",
    });
    React.useEffect(() => {
        if (response) {
            setResult(true);
        }
        if (error) {
            setResult(false);
        }
    }, [response, error]);
    return <React.Fragment />;
}

function SelectSearch({
    availableFields,
    fieldOptions,
    selectValueDefaults,
    selectOptionsURI,
}) {
    const [checkboxes, setCheckboxes] = React.useState(availableFields);
    React.useEffect(() => {
        Object.keys(checkboxes).forEach((k) => {
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

    const [selectValues, setSelectValues] = React.useState(fieldValues);
    // apply url search params to SelectInputs
    React.useEffect(() => {
        const newSelectValues = { ...selectValues };
        const newSelectOptions = { ...selectOptions };
        Object.entries(selectOptions).forEach(([k, values]) => {
            const paramOptions = searchParams
                .getAll(k)
                .filter((p) => p !== "" && p !== "on");
            if (paramOptions.length) {
                const fullItem = values.filter((v) =>
                    paramOptions.includes(v.value),
                );
                if (fullItem.length) {
                    newSelectValues[k].push(...fullItem);
                } else {
                    const temp = paramOptions.map((v) => ({
                        value: v,
                        label: v,
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
    const { response, loading, error } = useFetch(selectOptionsURI, {
        method: "GET",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        redirect: "manual",
    });
    // apply response to SelectInputs
    React.useEffect(() => {
        if (response) {
            newSelectOptions = { ...selectOptions };
            Object.entries(response).forEach(([k, v]) => {
                const map = v.map((e) => ({
                    value: e[k],
                    label: e[k],
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
    return (
        <SpeechRecogContext.Provider value={speechRecogStatus}>
            <fieldset className="form-group col-md-6 offset-md-3">
                <CheckSpeechRecogStatus
                    setResult={(e) => setSpeechRecogStatus(e)}
                />
                <FilterBy {...{ checkboxes, setCheckboxes }} />
                {loading && (
                    <div className="progress m-3" style={{ height: "3px" }}>
                        <div
                            className="progress-bar progress-bar-striped progress-bar-animated"
                            role="progressbar"
                            style={{ width: "90%" }}
                        ></div>
                    </div>
                )}
                <SelectInputMap
                    {...{
                        checkboxes,
                        selectValues,
                        selectOptions,
                        setSelectValues,
                    }}
                />
                <input
                    className="btn btn-link btn-primary btn-block btn"
                    name="submit"
                    type="submit"
                    value="Search"
                />
                {error && <p>Something went wrong...</p>}
            </fieldset>
        </SpeechRecogContext.Provider>
    );
}

userAvailableFields = {
    id: { label: "User ID", enabled: false },
    username: { label: "Username", enabled: false },
    firstname: { label: "First Name", enabled: false },
    lastname: { label: "Last Name", enabled: false },
    userType: { label: "User Type", enabled: false },
    email: { label: "Email", enabled: false },
    order_by: {
        label: "Order By",
        enabled: false,
        hide: true,
        single: true,
    },
};

userFieldOptions = {
    id: [],
    username: [],
    firstname: [],
    lastname: [],
    userType: [],
    email: [],
    order_by: [],
};

userSelectValueDefaults = {};

userSelectOptionsURI = "/api/users?search_data=all";

function UserSelectSearch() {
    return (
        <SelectSearch
            availableFields={userAvailableFields}
            fieldOptions={userFieldOptions}
            selectValueDefaults={userSelectValueDefaults}
            selectOptionsURI={userSelectOptionsURI}
        />
    );
}

carAvailableFields = {
    id: { label: "Car ID", enabled: false, voiceSearch: true },
    make: { label: "Make", enabled: false, voiceSearch: true },
    body_type: { label: "Body Type", enabled: false, voiceSearch: true },
    colour: { label: "Colour", enabled: false, voiceSearch: true },
    seats: { label: "Seats", enabled: false, voiceSearch: true },
    is_active: { label: "Available Only", enabled: false },
    order_by: {
        label: "Order By",
        enabled: true,
        hide: true,
        single: true,
    },
};

carFieldOptions = {
    id: [],
    make: [],
    body_type: [],
    colour: [],
    seats: [],
    order_by: [
        { label: "Price: Ascending", value: "price_asc" },
        { label: "Price: Descending", value: "price_desc" },
    ],
};

carSelectValueDefaults = {
    order_by: [{ label: "Price: Descending", value: "price_desc" }],
};

carSelectOptionsURI = "/api/cars?search_data=all";

function CarSelectSearch() {
    return (
        <SelectSearch
            availableFields={carAvailableFields}
            fieldOptions={carFieldOptions}
            selectValueDefaults={carSelectValueDefaults}
            selectOptionsURI={carSelectOptionsURI}
        />
    );
}

userReactSelect = document.getElementById("user-react-select");
if (userReactSelect) ReactDOM.render(<UserSelectSearch />, userReactSelect);

carReactSelect = document.getElementById("car-react-select");
if (carReactSelect) ReactDOM.render(<CarSelectSearch />, carReactSelect);
