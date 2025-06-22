import React, { useState, useEffect } from "react";
import { Button } from "@shadcn/ui";
import { Card, CardContent } from "@shadcn/ui";

function LoginPanel() {
    const [characterName, setCharacterName] = useState(null);

    useEffect(() => {
        fetch("/api/current_user")
            .then((res) => res.json())
            .then((data) => {
                if (data.character_name) {
                    setCharacterName(data.character_name);
                }
            })
            .catch(() => {
                setCharacterName(null);
            });
    }, []);

    const handleLoginClick = () => {
        window.location.href = "/auth/login";
    };

    const handleLogoutClick = () => {
        fetch("/auth/logout", { method: "POST" }).then(() => {
            setCharacterName(null);
            window.location.reload();
        });
    };

    if (!characterName) {
        return (
            <div className="flex justify-center items-center min-h-[250px]">
                <Card className="w-full max-w-sm bg-gradient-to-br from-blue-900 via-blue-800 to-blue-700 text-white shadow-lg">
                    <CardContent className="text-center">
                        <h2 className="text-2xl font-semibold mb-6">
                            Welcome to Neo Vortex
                        </h2>
                        <p className="mb-8">
                            Log in with your EVE Online account to manage your
                            stations and blueprints.
                        </p>
                        <Button
                            onClick={handleLoginClick}
                            className="bg-gradient-to-r from-indigo-500 via-purple-600 to-pink-600 hover:brightness-110 transition"
                        >
                            Log in with EVE Online
                        </Button>
                    </CardContent>
                </Card>
            </div>
        );
    }

    return (
        <div className="flex justify-center min-h-[100px] mt-6">
            <Card className="w-full max-w-md bg-gradient-to-br from-blue-900 via-blue-800 to-blue-700 text-white shadow-lg">
                <CardContent className="flex items-center justify-between">
                    <span className="text-lg font-semibold">
                        Welcome, {characterName}!
                    </span>
                    <Button
                        variant="outline"
                        onClick={handleLogoutClick}
                        className="border-white text-white hover:bg-white hover:text-blue-900 transition"
                    >
                        Logout
                    </Button>
                </CardContent>
            </Card>
        </div>
    );
}

export default LoginPanel;
