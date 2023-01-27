// ****************************************
// APPLICATION PAGE DECLARATION: /center.js
// ----------------------------------------
// Version: 1.00
// Date: 10-01-2023

default_submit_mode = 2;
default_action      = '800';
default_log_action  = '801';
default_input_name  = 'message_id';
default_menu_item   = '';

LINE    = 'messages';
SUBLINE = '';

// ----------------------
// Dialog Action Handlers
// ----------------------

function sidebar_callback() {
    $onInfoContainerChanged();
}

function subline_refresh(filename) {
}

function log_callback(current_action, data, props) {
}

// --------------
// Page Functions
// --------------

function $Init() {
    $SidebarControl.init(sidebar_callback, ['type', 'status', 'batchtype']);

    page_sort_title = $("#sort_icon").attr('title');

    SelectedReset();

    $LineSelector.init();
    $SidebarDialog.init();

    $TabSelector.init();

    tab_init('capacities', 0);
    tab_init('speeds', 0);

    init_controller('capacities');

    $PageController._init_state();

    // ------------------------
    // Start default log action
    // ------------------------

    interrupt(true, 1);
}

function $Confirm(mode, ob) {
    $ConfirmDialog.close();

    function _check(x) { 
        var errors = x['errors']; 

        //alert(errors.length);

        if (errors.length > 0) {
            var msg = errors.join('<br>');
            $ShowError(msg, true, true, false);
        }
        else {
            $NotificationDialog.open(keywords['Message:Request sent successfully']);
        }
    }

    switch (mode) {
        case 0:
            break;
        case 1:
    }
}

function $Notification(mode, ob) {
    $NotificationDialog.close();

}

function $ShowMenu(id, status, path) {
}

function $onTabSelect(group){
    $CenterSubmitDialog.activate(group);
}

function $onTablineSelect(ob, alias) {
}

function $onTablineUpload(alias) {
    //alert('$onTablineUpload.alias:'+alias);
    $Go('802');
    return 1;
}

function $onPaginationFormSubmit(frm) {
    return true;
}

function $onFilterFormSubmit(frm) {
    return true;
}

function $onInfoContainerChanged() {
    //alert($_width('screen-min')-$("#sidebarFrame").width()+':'+$("#line-table").width());
}

// ===========================
// Dialog windows declarations
// ===========================

function MakeFilterSubmit(mode, page) {
    //$("#filter-form").attr("action", baseURI);

    switch (mode) {

        // -------------
        // Submit modes:
        // -------------

        case 0:
        case 1:
        case 2:
            var division = $("select#division").val();
            $("input[name='division']").each(function() { $(this).val(division); });
        case 3:
            var line = $("select#line").val();
            $("input[name='line']").each(function() { $(this).val(line); });
        case 4:
        case 5:
            break;

        // ---------------------------
        // LineSelector Handler submit
        // ---------------------------

        case 9:
    }

    $ResetLogPage();

    $setPaginationFormSubmit(page);
    $onParentFormSubmit('filter-form');
}

function makeTodayRequest() {
    var date = new Date();
    var now = date.getToday();

    $_set_body_value('order-date-from', now);
    $onParentFormSubmit('filter-form');
}

// =========================
// Custom routine assigments
// =========================

// ====================
// Page Event Listeners
// ====================

jQuery(function($) 
{


    // --------------
    // Line selection
    // --------------

    $(".line").click(function(e) {
        if (is_show_error)
            return;

        $LineSelector.onRefresh($(this));
    });

    // -------------
    // Client events
    // -------------

    $("#period", this).on("click", function(e) {
        e.stopPropagation();
        //
        //  Show Diagram Node info
        //
        var ob = $(this);
        $PageController.show_period("over");
        //alert('click1:'+ob.attr('id'));
        e.stopPropagation();
    });

    // ---------------------
    // Data Section progress
    // ---------------------

    $("#data-section").on('click', '.column', function(e) {
        var ob = $(this);
        var parent = ob.parents("*[class*='line']").first();
        if (!is_null(parent) && !parent.hasClass("tabline") && !ob.hasClass("header"))
            $InProgress(ob, 1);
        //alert('click2:'+ob.attr());
    });

    // -----------------
    // Tabline selection
    // -----------------

    $(".column").on('click', function(e) {
        if (!$_mobile())
            return;

        e.stopPropagation();

        var ob = ($(this)).parent();
        var id = ob.attr('id');

        if (IsTrace)
            alert('mobile.click.column:'+id);

        $PageScroller.init_state(ob);

        if (id.indexOf('capacties') > -1 || id.indexOf('speeds') > -1)
            $PageController.show_line(ob, true, 1);
    });

    $("#data-section").on('click', '.column', function(e) {
        //
        //  Tabline Columns click
        //
        var ob = ($(this)).parent();
        var id = ob.attr('id');

        if (IsTrace)
            alert('main.click.column:'+id);

        $PageScroller.init_state(ob);

        if (id.indexOf('capacties') > -1 || id.indexOf('speeds') > -1)
            $PageController.show_line(ob, true, 0);
    });

    // -----------------
    // Page Form Buttons
    // -----------------

    // -------------
    // Resize window
    // -------------

    $(window).on("resize", function() {
        $PageScroller.reset(1, 1000);
    });

    $(window).scroll(function(e){
        //$PageScroller.checkPosition(0);
    });

    // --------
    // Keyboard
    // --------

    $(window).keydown(function(e) {
        if ($ConfirmDialog.is_focused() || $NotificationDialog.is_focused())
            return;

        if (is_show_error)
            return;

        if (e.keyCode==13) {                                     // Enter
            // ------------------------------------
            // Bankpesro Submit Dialog Class Events
            // ------------------------------------
            if ($CenterSubmitDialog.is_focused()) {
                $CenterSubmitDialog.confirmed();
                e.preventDefault();
                return false;
            }
        }

        if ($CenterSubmitDialog.is_focused() || is_search_focused)
            return;

        var exit = false;

        if (IsTrace && IsDeepDebug)
            alert(e.ctrlKey+':'+e.shiftKey+':'+e.altKey+':'+e.keyCode);

        exit = true;
        
        if (e.shiftKey && e.keyCode==9)                          // Shift-Tab
            init_controller(null);

        if (e.shiftKey && e.keyCode==80) {                       // Shift-P
            exit = true;
        }

        else if (e.shiftKey && e.keyCode==79) {                  // Shift-O
            e.stopPropagation();
            $SidebarDialog.activate($(this));
            exit = true;
        }
        
        // -----------------------
        // Tabline Selector moving
        // -----------------------

        else if (selector.active) {
            if (e.keyCode==38)                                  // Up
                    $PageScroller.refresh(null, 'up');
            else if (e.keyCode==40)                             // Down
                $PageScroller.refresh(null, 'down');
            else if (e.keyCode==36)                             // Home
                $PageScroller.refresh(null, 'first');
            else if (e.keyCode==33)                             // PgUp
                $PageScroller.refresh(null, 'pgup');
            else if (e.keyCode==34)                             // PgDown
                $PageScroller.refresh(null, 'pgdown');
            else if (e.keyCode==35)                             // End
                $PageScroller.refresh(null, 'last');
        }

        if (exit) {
            e.preventDefault();
            return false;
        }
    });
});

function sidebar_submit() {
    if (IsDeepDebug) {
        alert('sidebar_submit.state:'+$("#sidebar").val());
    }
}

function page_is_focused(e) {
    return $CenterSubmitDialog.is_focused();
}

function $_show_page(mode) {
    $ShowPage(mode);
}

function resize(force) {
    if ($_mobile() && force) {
        //show_width();
        //show_height();

        var viewportW = verge.viewportW();
        var viewportH = verge.viewportH();

        //alert(viewportW+':'+ viewportH);
    }
}

// =======
// STARTER
// =======

$(function() 
{
    if (IsTrace)
        alert('Document Ready (center)');

    IsLog = 1;
    IsDebug = 0;
    IsDeepDebug = 0;
    IsTrace = 0;

    current_context = 'center';

    if (!is_empty(search_title))
        $("#search-context").attr("placeholder", search_title);
    //$("#batchtype").css("width", $("#status").width()+"px");
    //$("#batchtype").width($("#status").width());

    IsActiveScroller = 0;

    resize(1);

    $_init();
});
