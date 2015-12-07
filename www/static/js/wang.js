// awesome.js

function showError(err) {
    //var alert = $();
    if (err) {
        //alert.text(err.message || err.error || err).removeClass('uk-hidden').show();
        try {
            //if (alert.offset().top < ($(window).scrollTop() - 41)) {
            //    $('html,body').animate({scrollTop: alert.offset().top - 41});
            alert(err);
			//}
        }
        catch (e) {}
    }
    //else {
        //alert.addClass('uk-hidden').hide().text('');
    //}
}

function _httpJSON(method, url, data, callback) {
    var opt = {
        type: method,
        dataType: 'json'
    };
    if (method==='GET') {
        opt.url = url + '?' + data;
    }
    if (method==='POST') {
        opt.url = url;
        opt.data = JSON.stringify(data || {});
        opt.contentType = 'application/json';
    }
    $.ajax(opt).done(function (r) {
        if (r && r.error) {
            return callback(r);
        }
        return callback(null, r);
    }).fail(function (jqXHR, textStatus) {
        return callback({'error': 'http_bad_response', 'data': '' + jqXHR.status, 'message': '网络好像出问题了 (HTTP ' + jqXHR.status + ')'});
    });
}


function getJSON(url, data, callback) {
    if (arguments.length===2) {
        callback = data;
        data = {};
    }
    if (typeof (data)==='object') {
        var arr = [];
        $.each(data, function (k, v) {
            arr.push(k + '=' + encodeURIComponent(v));
        });
        data = arr.join('&');
    }
    _httpJSON('GET', url, data, callback);
}

function postJSON(url, data, callback) {
    if (arguments.length===2) {
        callback = data;
        data = {};
    }
    _httpJSON('POST', url, data, callback);
}

// add to prototype:

if (! String.prototype.trim) {
    String.prototype.trim = function() {
        return this.replace(/^\s+|\s+$/g, '');
    };
}

if (! Number.prototype.toDateTime) {
    var replaces = {
        'yyyy': function(dt) {
            return dt.getFullYear().toString();
        },
        'yy': function(dt) {
            return (dt.getFullYear() % 100).toString();
        },
        'MM': function(dt) {
            var m = dt.getMonth() + 1;
            return m < 10 ? '0' + m : m.toString();
        },
        'M': function(dt) {
            var m = dt.getMonth() + 1;
            return m.toString();
        },
        'dd': function(dt) {
            var d = dt.getDate();
            return d < 10 ? '0' + d : d.toString();
        },
        'd': function(dt) {
            var d = dt.getDate();
            return d.toString();
        },
        'hh': function(dt) {
            var h = dt.getHours();
            return h < 10 ? '0' + h : h.toString();
        },
        'h': function(dt) {
            var h = dt.getHours();
            return h.toString();
        },
        'mm': function(dt) {
            var m = dt.getMinutes();
            return m < 10 ? '0' + m : m.toString();
        },
        'm': function(dt) {
            var m = dt.getMinutes();
            return m.toString();
        },
        'ss': function(dt) {
            var s = dt.getSeconds();
            return s < 10 ? '0' + s : s.toString();
        },
        's': function(dt) {
            var s = dt.getSeconds();
            return s.toString();
        },
        'a': function(dt) {
            var h = dt.getHours();
            return h < 12 ? 'AM' : 'PM';
        }
    };
    var token = /([a-zA-Z]+)/;
    Number.prototype.toDateTime = function(format) {
        var fmt = format || 'yyyy-MM-dd hh:mm'
        var dt = new Date(this * 1000);
        var arr = fmt.split(token);
        for (var i=0; i<arr.length; i++) {
            var s = arr[i];
            if (s && s in replaces) {
                arr[i] = replaces[s](dt);
            }
        }
        return arr.join('');
    };
}



function refresh() {
    var
        t = new Date().getTime(),
        url = location.pathname;
    if (location.search) {
        url = url + location.search + '&t=' + t;
    }
    else {
        url = url + '?t=' + t;
    }
    location.assign(url);
}



function showConfirm(title, text, fn_ok, fn_cancel) {
    var s = '<div id="div-confirm" class="uk-modal">' +
            '<div class="uk-modal-dialog">' +
            '<a href="#0" class="uk-modal-close uk-close"></a>' +
            '<h1 class="x-title"></h1>' +
            '<p class="x-text"></p>' +
            '<hr><p class="uk-text-center">' +
            '<button class="uk-button uk-button-primary x-ok"><i class="uk-icon-check"></i> 是</button>' +
            '&nbsp;&nbsp;&nbsp;' +
            '<button class="uk-button x-cancel"><i class="uk-icon-times"></i> 否</button>' +
            '</p></div></div>';
    $('body').append(s);
    var m = $('#div-confirm');
    var modal = new $.UIkit.modal.Modal('#div-confirm');
    m.find('.x-title').text(title);
    m.find('.x-text').text(text);
    m.find('.x-ok').click(function () {
        modal.hide();
        fn_ok && fn_ok();
    });
    m.find('.x-cancel').click(function () {
        modal.hide();
        fn_cancel && fn_cancel();
    });
    m.on({
        'uk.modal.hide': function() {
            $('#div-confirm').remove();
        }
    });
    modal.show();
}


$(function() {
    if (location.pathname === '/' || location.pathname.indexOf('/blog')===0) {
        $('li[data-url=blogs]').addClass('uk-active');
    }
});


function _display_error($obj, err) {
    if ($obj.is(':visible')) {
        $obj.hide();
    }
    var msg = err.message || String(err);
    var L = ['<div class="uk-alert uk-alert-danger">'];
    L.push('<p>Error: ');
    L.push(msg);
    L.push('</p><p>Code: ');
    L.push(err.error || '500');
    L.push('</p></div>');
    $obj.html(L.join('')).slideDown();
}

function error(err) {
    _display_error($('#error'), err);
}

function fatal(err) {
    _display_error($('#loading'), err);
}