# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

"""
This module demonstrates how to load the streaming extensions via Python. Just change the extension list to modify this to load any extensions you like via Python.

Version: 1.0.0
"""

import omni.kit.app


manager = omni.kit.app.get_app().get_extension_manager()
extensions = ['omni.kit.livestream.messaging', 'omni.kit.livestream.webrtc.setup', 'omni.services.streamclient.webrtc']
for extension in extensions:
    manager.set_extension_enabled_immediate(extension, True)
