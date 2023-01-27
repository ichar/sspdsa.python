// ********************************
// HELPER FUNCTION CONTROLS MANAGER
// --------------------------------
// Version: 1.0
// Date: 04-07-2017

// =======================
// Component control class
// =======================

var $LocalPageScroller = {
    page      : { 'base':null, 'top':0, 'height':0 },
    control   : { 'ob':null, 'default_position':0, 'top':0, 'height':0, 'isDefault':0, 'isMoved':0, 'isShouldBeMoved':0 },
    position  : 0,

    IsDebug : 0, IsTrace : 0, IsLog : 0,

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

var $SidebarDialog = {
    pointer       : null,
    ob            : null,

    IsDebug : 0, IsTrace : 0, IsLog : 0,

    done_action   : null,
    is_active     : null,
    top           : null,
    screen_height : null,

    period_top : 0,

    is_shown      : 1,
    is_activated  : 0,

    init: function() {
        this.pointer = $("#sidebarPointer");
        this.is_active = true;
    },

    activate: function(ob) {
        this.ob = ob;
        this.is_activated = 1;

        $SidebarControl.onNavigatorClick(0, this.done_action);
    },

    clear: function() {
    },

    refreshed: function(x) {
        var self = $SidebarDialog; 

        if (this.IsTrace)
            alert('$SidebarDialog.refreshed');
    },

    resize: function() {
        $PageController.updateLog();
    },

    done: function(link) {
        if (this.IsDebug)
            alert('$SidebarDialog.done:'+link);

        if (!is_empty(link)) {
            $onPageLinkSubmit(link);
        }
        else
            this.resize();
    },
};

var $PageController = {
    callbacks : null,
    container : null,
    group : '',

    timer : null,

    IsDebug : 0, IsTrace : 0, IsLog : 0,

    init: function(action, default_action) {
        this.group = selector.group || 'configs';
        if (this.IsTrace)
            alert('configurator.$PageController.init: '+action+':'+default_action);
    },

    _init_state: function() {
        if (this.IsLog)
            console.log('configurator.$PageController._init_state:');
    },

    reset: function(force) {},

    trace: function(force) {},

    default_action: function(action, args) {
        if (action == default_action) {
            ObjectUpdate(args, {
                'change_id' : SelectedGetItem(this.group, 'id'),
                'row_id' :  selector.id,
                'param_status' : '',  //$("#paramstatus").val()
                'group' : selector.group
            });
        }
        return action;
    },

    action: function(action, args, params) {
        if (action > default_action) {
            var group = selector.group;
            var mode = selector.mode;
            ObjectUpdate(args, {
                'action' : action,
                'command': $("#command").val(),
                'change_id' : SelectedGetItem(group, 'id'),
                'group' : group,
                'mode' : mode, 
                'row_id' :  selector.id,
                'content' : $("#config_content").val(),
            });

            if (this.IsTrace)
                alert('configurator.$PageController.action:'+action+', group:'+this.group+', change_id:'+args.change_id);

            if (this.IsLog)
                console.log('configurator.$PageController.action:', action, args);
        }
    },

    updateView: function(action, callbacks, response, props, total) {
        if (this.IsLog)
            console.log('configurator.$PageController.updateView', action, response, props, total);

        var group = getattr(props, 'group', selector.group);
        var mode = getattr(props, 'mode', selector.mode);

        var change_id = getattr(props, 'change_id');
        var row_id = getattr(props, 'row_id');
        var total_html = getattr(props, 'total');
        var chunk = getattr(props, 'chunk');
        var next_row = getattr(props, 'next_row');
        var group = this.group;

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
            case default_action:
                tab_id = group+"-container";
                this.container = $("#tabline-"+group);
                template ='<table class="view-data p100" id="'+tab_id+'" border="1"><thead><tr>';
                row_class_name = 'tabline-'+group;
                only_columns = 'all';
                column_class_prefix = 'log-';
                rows_counting = $("#"+group+"-rows-total");
                set_table(this.container, row_class_name, template, only_columns, column_class_prefix,
                    rows_counting, 
                    total_html,
                    get_chunk_begin(chunk)
                    );
                $PageController.activate(group, row_id, next_row, chunk);
                break;
            case default_log_action:
                mid = '';
                break;
        }
        return mid;
    },

    sleep: function(callback, timeout) {
        if (this.IsDebug)
            alert('configurator.$PageController.sleep:'+timeout);
        this.timer = setTimeout(callback, timeout);
    },

    clear_timeout: function() {
        if (!is_null(this.timer)) {
            clearTimeout(timer);
            this.timer = null;
        }
    },

    activate: function(group, row_id, next_row, chunk) {
        this.clear_timeout();

        if (this.IsLog)
            console.log('configurator.$PageController.activate.before:', group, row_id, this.container);

        $PageScroller.activate(group, row_id, next_row, chunk);
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

    updateLog: function(action, response) {
        if (this.IsTrace)
            alert('configurator.$PageController.updateLog:'+action+', group:'+this.group);

        var change_id = getattr(response,'change_id');
        var row_id = getattr(response,'row_id');
        var props = response['props'];
        var data = getattr(props, 'changes');

        var group = getattr(props, 'group', this.group) || selector.group;

        if (this.IsLog) {
            console.log('configurator.$PageController.updateLog:', action, change_id, row_id, selector.id);
        }

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

        var ob = $("#config_content");

        if (this.IsLog)
            console.log('configurator.$PageController.updateLog.textarea:', ob);

        ob.val(getattr(props, 'content', ''));

        selector.row_id = row_id;

        if (change_id != SelectedGetItem(group, 'id')) {
            //this.sleep(function() { $PageController.activate(group, change_id); }, default_timeout);
            this.activate(group, change_id);
            //init_controller();
        }
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
            alert('configurator.$PageLoader.init:'+$LineSelector.get_id()+':'+$LineSelector.get_current().get(0).outerHTML);

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
            alert(['configurator.$PageLoader.scroll', this.scroll_mode, this.line['state_is_open'], this.scroll_top, this.height, int(this.top), int(current_top)].join(':'));

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
                    alert('configurator.$PageLoader.remove_current: Error');
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
            console.log('configurator.$PageLoader.set, mode:', this.mode, data, x);

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

    check_reference: function(x) {
    },

    check_paid: function(info) {
    },

    check_refers: function(info) {
    },

    check_images: function(currentfile) {
    },

    set_status: function(status) {
    },

    set_barcode: function(props) {
    },

    update_param_combo: function(x) {
        this.check(x);

        if (!this.is_error) {
            var values = x['data'];
            var current_value = x['props'][0];
            var options = this.box.prop("options");

            if (!is_null(options)) {
                $('option', this.box).remove();

                values.forEach(function(value, index) {
                    var option = new Option(value, value, false, false);
                    options[options.length] = option;
                });
            }

            if (current_value)
                $("#param_value_combo").val(current_value);
        }

        //this._reset();
        this._after();
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
             //'content': $("#config_content").val(),
             'command': command,
        });

        this._before(ob, command);

        $Handle(action, function(x) { $PageLoader.refresh_after_change(x); }, params);
    },

    handle_refresh: function(action, ob, command) {
        this.action = action;
        this.mode = 'refresh';

        var params = {'command':command};

        $Handle(this.action, function(x) { $PageLoader.refresh_after_change(x); }, params);
    },

    select_item: function(action, ob, command) {
    },

    disable_edit: function(props) {
    },

    disable_review: function(props) {
    },

    disable_statuses: function(props) {
    },

    _register: function() {
        this.container = $("#"+selected_review_id);
        
        this.line['id'] = $LineSelector.get_id();

        if (is_no_line_open)
            this.container.addClass('closed');

        this.line['state_is_open'] = is_no_line_open ? 0 : 1;

        is_no_line_open = 0;
    },

    is_activated: function() {
        return this.line['state_is_open'] == -1 ? true : false;
    },

    activate: function(ob) {
        var line_id = $_get_item_id(ob);

        if (this.IsDeepDebug)
            alert(['configurator.$PageLoader.activate', 
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

    refresh_line: function(action, response, line) {
        if (this.IsLog)
            console.log('$PageLoader.refresh_line', response);

        var data = getattr(response, 'data', null);
        var columns = getattr(response, 'columns', null);
        var props = getattr(response, 'props', null);

        if (is_null(line))
            line = $LineSelector.get_current();

        $PageController.updateLog(action, response);

        this._after();
    },

    refresh_status: function(response) {
    },

    refresh_after_change: function(response) {
        if (this.IsTrace)
            alert('configurator.$PageLoader.refresh_after_change');

        if (this.IsLog)
            console.log('$PageLoader.refresh_after_change', response);

        var action = getattr(response, 'action', default_action);

        if (!is_null(response)) {
            var props = getattr(response, 'props', null);
            var total = parseInt(getattr(response, 'total', '0'));
            var status = getattr(response, 'status', null);
            var path = getattr(response, 'path', null);;

            selected_menu_action = action;

            if (action == default_action) {
                $updateViewData(action, response, props, total, status, path);
            }

            $PageController.updateLog(default_log_action, response);
        }
    },

    refresh: function(response) {
        /***
         *  Called by default_handler, action:default_log_action
         */
        if (this.IsTrace)
            alert('configurator.$PageLoader.refresh');

        this.reset();

        var current_action = default_action;

        this.init();

        this.remove_current();

        var columns = response['columns'];
        var colspan = columns.length || 10;

        this.refresh_after_change(response);

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
