#!/usr/bin/env bash
set -u

script_dir=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
bridge="$script_dir/steam-wayland-pointer.sh"
deck_ip=${STEAM_DECK_IP:-192.168.1.206}
bus_id=${STEAM_DECK_BUS_ID:-3-3}

controller_connected() {
	local device vendor product
	for device in /sys/bus/usb/devices/*; do
		[[ -r $device/idVendor && -r $device/idProduct ]] || continue
		read -r vendor < "$device/idVendor"
		read -r product < "$device/idProduct"
		[[ $vendor == 28de && $product == 1205 ]] && return 0
	done
	return 1
}

bridge_running() {
	"$bridge" status >/dev/null 2>&1
}

refresh_waybar() {
	pkill -RTMIN+9 waybar 2>/dev/null || true
}

status_json() {
	local controller_state bridge_state class text tooltip

	if controller_connected; then
		controller_state="connected"
		text="󰊗 ✓"
	else
		controller_state="disconnected"
		text="󰊗 ×"
	fi

	if bridge_running; then
		bridge_state="running"
	else
		bridge_state="stopped"
	fi

	case "$controller_state:$bridge_state" in
		connected:running)
			class="ready"
			;;
		connected:stopped)
			class="no-bridge"
			;;
		disconnected:running)
			class="bridge-only"
			;;
		*)
			class="disconnected"
			;;
	esac

	tooltip="Steam Deck controller: $controller_state"
	tooltip+=$'\n'"Wayland pointer bridge: $bridge_state"
	tooltip+=$'\n'"Deck: $deck_ip ($bus_id)"
	tooltip+=$'\n\nClick for controls'
	jq -cn --arg text "$text" --arg tooltip "$tooltip" --arg class "$class" \
		'{"text":$text,"tooltip":$tooltip,"class":$class}'
}

run_privileged_action() {
	local action=$1
	shift
	if [[ $action == Connection ]]; then
		STEAM_DECK_NONINTERACTIVE=1 "$@"
	else
		SUDO_ASKPASS="$script_dir/waybar-sudo-askpass.sh" sudo -A -- "$@"
	fi
}

run_controller_action() {
	local action=$1 log_file detail
	shift
	log_file="${XDG_RUNTIME_DIR:-/tmp}/steam-deck-controller-action.log"
	printf '%s: %s\n\n' "$(date '+%F %T')" "$action" > "$log_file"

	if run_privileged_action "$action" "$@" >> "$log_file" 2>&1; then
		notify-send "Steam Deck controller" "$action succeeded"
	else
		detail=$(awk 'NF { line=$0 } END { print line }' "$log_file")
		notify-send --urgency=critical "Steam Deck controller" \
			"$action failed${detail:+: $detail}"
		zenity --text-info \
			--title="Steam Deck controller — $action failed" \
			--filename="$log_file" \
			--width=720 --height=420 --ok-label="Close" 2>/dev/null || true
		return 1
	fi
}

show_menu() {
	local options=() selection

	if controller_connected; then
		options+=("Disconnect Steam Deck controller")
	else
		options+=("Connect Steam Deck controller")
	fi

	if bridge_running; then
		options+=("Stop Wayland pointer bridge" "Restart Wayland pointer bridge")
	else
		options+=("Start Wayland pointer bridge")
	fi

	options+=("Refresh status" "Open bridge log")
	selection=$(printf '%s\n' "${options[@]}" | fuzzel --dmenu \
		--no-exit-on-keyboard-focus-loss \
		--hide-prompt --width=38 --lines="${#options[@]}" \
		--background-color=11111bf2 \
		--text-color=cdd6f4ff \
		--prompt-color=b4befeff \
		--input-color=f5e0dcff \
		--match-color=cba6f7ff \
		--selection-color=cba6f7ff \
		--selection-text-color=11111bff \
		--selection-match-color=313244ff \
		--border-color=b4befeff \
		--border-width=2 \
		--selection-radius=8) || exit 0

	case $selection in
		"Connect Steam Deck controller")
			run_controller_action "Connection" "$script_dir/pc-connect.sh" "$deck_ip" "$bus_id"
			;;
		"Disconnect Steam Deck controller")
			run_controller_action "Disconnection" "$script_dir/pc-disconnect.sh"
			;;
		"Start Wayland pointer bridge")
			"$bridge" start
			;;
		"Stop Wayland pointer bridge")
			"$bridge" stop
			;;
		"Restart Wayland pointer bridge")
			"$bridge" stop
			"$bridge" start
			;;
		"Open bridge log")
			ghostty --title="Steam Wayland Pointer Log" -e tail -f "${XDG_RUNTIME_DIR:-/tmp}/steam-wayland-pointer.log" &
			;;
	esac

	sleep 0.2
	refresh_waybar
}

case ${1:-status} in
	status) status_json ;;
	menu) show_menu ;;
	connect)
		run_controller_action "Connection" "$script_dir/pc-connect.sh" "$deck_ip" "$bus_id"
		refresh_waybar
		;;
	disconnect)
		run_controller_action "Disconnection" "$script_dir/pc-disconnect.sh"
		refresh_waybar
		;;
	bridge-start)
		"$bridge" start
		refresh_waybar
		;;
	bridge-stop)
		"$bridge" stop
		refresh_waybar
		;;
	bridge-restart)
		"$bridge" stop
		"$bridge" start
		refresh_waybar
		;;
	log)
		ghostty --title="Steam Wayland Pointer Log" -e tail -f "${XDG_RUNTIME_DIR:-/tmp}/steam-wayland-pointer.log" &
		;;
	refresh) refresh_waybar ;;
	*)
		echo "Usage: $0 {status|menu|connect|disconnect|bridge-start|bridge-stop|bridge-restart|log|refresh}" >&2
		exit 2
		;;
esac
