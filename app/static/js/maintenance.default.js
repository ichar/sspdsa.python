// ********************************
// HELPER FUNCTION CONTROLS MANAGER
// --------------------------------
// Version: 1.0
// Date: 04-07-2017

// =======================
// Component control class
// =======================

var $PageScroller = {
    page      : { 'base':null, 'top':0, 'height':0 },
    control   : { 'ob':null, 'default_position':0, 'top':0, 'height':0, 'isDefault':0, 'isMoved':0, 'isShouldBeMoved':0 },
    position  : 0,
    is_trace  : 0,

    init: function() {
    },

    reset: function(force) {
    },

    trace: function(force) {
    },

    checkPosition: function(reset) {
    },

    move: function() {
    }
};

var $PageController = {
    callbacks : null,

    IsDebug : 0, IsTrace : 0, IsLog : 0,

    init: function(action, default_action) {
        if (this.IsTrace)
            alert('maintenance.$PageController.init: '+action+':'+default_action);
    },

    reset: function(force) {},

    trace: function(force) {},

    default_action: function(action, args) {
        if (action == default_action) {
            ObjectUpdate(args, {
                'change_id' : SelectedGetItem(LINE, 'id'),
                'param_id' : '',  //$("#paramtype").val()
                'param_status' : '',  //$("#paramstatus").val()
            });
        }
        return action;
    },

    action: function(action, args) {
        if (action > default_action) {

            ObjectUpdate(args, {
                'action' : action,
                'command': $("#command").val(),
                'content': $("#config_content").val(),
                'change_id' : SelectedGetItem(LINE, 'id'),
                'param_id'  :  '', //SelectedGetItem(SUBLINE, 'id')
            });
        }
    },

    updateView: function(action, callbacks) {
        this.callbacks = callbacks;
        mid = '';
        //
        //  Update(refresh) view table content
        //
        set_table = this.callbacks['set_table'];
        switch (action) {
            //
            //  container : target control (table) for update
            //  template : template for table tag of target control
            //  row_class_name : css class name for row
            //  only_columns : mask['all'|'simple'|1], 
            //        'all' - for every columns, used TEMPLATE_TABLINE_COLUMN
            //        'any' - for every columns, used TEMPLATE_TABLINE_COLUMN_SIMPLE; 
            //        1 - for given ones only 
            //  look 550 of log.default.js
            //  column_class_prefix - prefix for column class name
            //  row_counting - page total control (Total records)
            //  mid : menu id for $ShowMenu, if empty -- no menu
            case '400':
                container = $("#line-table");
                template ='<table class="view-data boxShadow1 configs" id="line-table" border="1">';
                row_class_name = 'line';
                only_columns = 'all';
                column_class_prefix = '';
                rows_counting = $("#configs_row_counting");
                set_table(container, row_class_name, template, only_columns, column_class_prefix, rows_counting);
                break;
            case '401':
                //set_table($("#line-table"), 'tabline');
                mid = '';
                break;
        }
        return mid;
    },

    html: function(ob, data) {
        if (!is_exist(ob)) 
            return;

        ob.html('');
        data.split(/\r?\n|\r|\n/g).forEach(function(x) {
            ob.append("<p>"+x+"</p>");
        });
        ob.append("<br>");
    },

    updateLog: function(data, props) {
        if (this.IsLog)
            console.log('maintenance.$PageController.updateLog:', data, props);

        if (!is_null(getattr(props, 'selected_row', null))) {
            before = getattr(props, 'before', '...');
            after = getattr(props, 'after', '...');
        } else {
            before = getattr(data[0], 'BEFORE', '...');
            after = getattr(data[0], 'AFTER', '...');
        }

        if (this.IsDebug)
            alert(typeof(data)+':'+is_null(data)+':'+before+' : '+after);

        this.html($("#changes_before"), before);
        this.html($("#changes_after"), after);

    },

    move: function() {
    }
};


// Current review container ID
var selected_review_id = 'subline_review';
// Size for scroll after activate
var window_scroll = 0;
// Page scroll mode by default
var default_scroll_mode = 'on-place';

var $PageLoader = {
    container   : null,
    actions     : {'change':'402'},

    IsDebug : 0, IsDeepDebug : 0, IsTrace : 0, IsLog : 0,

    action      : null,
    id          : null,
    command     : '',
    mode        : '',
    box         : null,
    
    scroll_mode : '',
    scroll_top  : 0,
    top         : 0,
    height      : 0,

    is_error    : false,
    is_shown    : false,
    is_locked   : false,

    line        : {'id' : null, 'state_is_open' : -1},

    init: function() {
        this.container = $("#"+selected_review_id);

        if (this.IsTrace)
            alert('maintenance.$PageLoader.init:'+$LineSelector.get_id()+':'+$LineSelector.get_current().get(0).outerHTML);

        this.line['id'] = null;

        is_full_container = 1;

        this.scroll_top = $(window).scrollTop();
    },

    reset: function() {
        this._show();
        this._reset();

        this.scroll_top = $(window).scrollTop();
    },

    scroll: function() {
        if (window_scroll != null) {
            $(window).scrollTop(window_scroll || 0);

            window_scroll = null;

            $_show_page(0);
            return;
        }

        var current_top = $LineSelector.get_current().position().top;

        if (this.IsDebug)
            alert(['maintenance.$PageLoader.scroll', this.scroll_mode, this.line['state_is_open'], this.scroll_top, this.height, int(this.top), int(current_top)].join(':'));

        if (this.top == 0 || this.height == 0 || this.top > current_top)
            return;

        var offset = 5;

        switch (this.scroll_mode) {
            case 'top':
                $(window).scrollTop(current_top - offset);
                break;
            case 'on-place':
                if (this.line['state_is_open'] != 0) {
                    var x = this.scroll_top - this.height - offset;
                    if (x > 0)
                        $(window).scrollTop(x);
                }
                break;
            default:
                break;
        }

        this.scroll_mode = '';
    },

    remove_current: function() {
        if (!is_null(this.container)) {
            try {
                this.top = this.container.position().top;
                this.height = this.container.height();
            } 
            catch(e) {
                if (this.IsTrace) 
                    alert('maintenance.$PageLoader.remove_current: Error');
                this.height = 0;
            }
            this.container.remove();
        }
    },

    _lock: function() {
        this.is_locked = true;
    },

    _unlock: function() {
        this.is_locked = false;
    },

    locked: function() {
        return this.is_locked;
    },

    _before: function(ob, command) {
        should_be_updated = false;
        selected_menu_action = default_log_action;

        this.box = ob;
        this.command = command;

        if (!is_null(this.command)) {
            if (this.command.toLowerCase().search('add') > -1)
                this.id = null;
            else
                this.id = $TablineSelector.get_id();
        }

        $InProgress(ob, 1);

        this.is_error = false;
    },

    _reset: function() {
        this.action = null;
        this.id = null;
        this.mode = null;
        this.box = null;
    },

    _hide: function() {
        if (is_empty(this.mode))
            return;

        var key = this.mode.toUpperCase();

        this.is_shown = true;
    },

    _show: function() {
        if (is_empty(this.mode))
            return;

        var key = this.mode.toUpperCase();

        this.is_shown = false;
    },

    _clean: function() {
    },

    set: function(x) {
        var data = x['data']['data'][0];

        if (this.IsLog)
            console.log('maintenance.$PageLoader.set, mode:', this.mode, data, x);

        switch (this.mode) {
        case 'param':
            $("#param").val(data['ParamID']);
            $("#new_param").val('');
            //$("#param_value").val(data['Value']);

            check_param(data['Value'], 0);
            break;
        }

        this._hide();
        this._after();
    },

    get: function(action, ob, command) {
        this.action = action;
        this.mode = command.split('_')[1].toLowerCase();

        this._before(ob, command);

        var params = {'command':command, 'id':this.id};

        $Handle(this.action, function(x) { $PageLoader.set(x); }, params);
    },

    cancel: function(action, ob, command) {
        this._clean();
        this._show();
        this._after();
    },

    check: function(x) {
        var errors = x['errors'];

        if (this.IsLog)
            console.log('$PageLoader.check, errors:', errors.length);

        if (!is_null(errors) && errors.length > 0) {
            var msg = errors.join('<br>');
            $ShowError(msg, true, true, false);
            this.is_error = true;

            this._show();
        }
    },

    handle: function(x) {
        this._reset();
        this._after();
    },

    handle_change: function(ob, command) {
        if (this.IsLog)
            console.log('$PageLoader.handle_change', ob, command);

        action = this.actions.change;

        params = Object.assign(default_params, {
             'content': $("#config_content").val(),
             'command': command,
        });

        this._before(ob, command);

        $Handle(action, function(x) { $PageLoader.refresh_after_review(x); }, params);
    },

    handle_refresh: function(action, ob, command) {
        this.action = action;
        this.mode = 'refresh';

        var params = {'command':command};

        $Handle(this.action, function(x) { $PageLoader.refresh_after_review(x); }, params);
    },

    select_item: function(action, ob, command) {
    },

    is_activated: function() {
        return this.line['state_is_open'] == -1 ? true : false;
    },

    activate: function(ob) {
        var line_id = $_get_item_id(ob);

        if (this.IsDeepDebug)
            alert(['maintenance.$PageLoader.activate', 
                this.line['id'], 
                line_id, 
                this.container.attr('id'), ob.position().top].join(':')
                );

        if (this.line['id'] == line_id) {
            if (this.line['state_is_open'] == 1) {
                this.container.addClass('closed');
                this.line['state_is_open'] = 0;
            }
            else if (this.line['state_is_open'] == 0) {
                this.container.removeClass('closed');
                this.line['state_is_open'] = 1;
            }
            return;
        }

        this.scroll_mode = default_scroll_mode;

        this._lock();

        $LineSelector.onRefresh(ob);
    },

    refresh_line: function(response, line) {
        if (this.IsLog)
            console.log('$PageLoader.refresh_line', response);

        var data = getattr(response, 'data', null);
        var columns = getattr(response, 'columns', null);
        var props = getattr(response, 'props', null);

        if (is_null(line))
            line = $LineSelector.get_current();

        $PageController.updateLog(data, props);

        this._after();
    },

    refresh_status: function(response) {
    },

    refresh_after_review: function(response) {
        if (this.IsTrace)
            alert('maintenance.$PageLoader.refresh_after_review');

        if (this.IsLog)
            console.log('$PageLoader.refresh_after_review', response);

        if (!is_null(response)) {
            var action = getattr(response, 'action', default_action);
            var props = getattr(response, 'props', null);
            var total = parseInt(getattr(response, 'total', '0'));
            var status = getattr(response, 'status', null);
            var path = getattr(response, 'path', null);;

            selected_menu_action = action

            if (action == default_action) {
                $updateLineData(action, response, props, total, status, path);
            }
            else if (action == default_log_action) {
                $updateSublineData(action, response, props, total, status, path);
            }

            this.refresh_line(response);
        }
    },

    refresh: function(response) {
        /***
         *  Called by default_handler, action:default_log_action
         */
        if (this.IsTrace)
            alert('maintenance.$PageLoader.refresh');

        this.reset();

        var current_action = default_action;

        this.init();

        this.remove_current();

        var columns = response['columns'];
        var colspan = columns.length || 10;

        this.refresh_after_review(response);

        if (this.IsLog)
            console.log('$PageLoader.refresh, selected_data_menu_id:', selected_data_menu_id);

        if (!is_full_container)
            this.scroll();

        this._unlock();

        this._after();

        this._register();

        if (!search_is_empty())
            return;
    },

    _after: function() {
        selected_menu_action = default_log_action;
        isCallback = false;
    }
};
