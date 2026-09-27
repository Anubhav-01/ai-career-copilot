"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { FieldError, Input, Label } from "@/components/ui/input";
import { useToast } from "@/components/ui/toast";
import { ApiError, api, tokenStore } from "@/lib/api";

const passwordSchema = z.object({
  current_password: z.string().min(1, "Required"),
  new_password: z.string().min(8, "At least 8 characters").max(128),
});

type PasswordValues = z.infer<typeof passwordSchema>;

export default function SettingsPage() {
  const { toast } = useToast();
  const router = useRouter();
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deletePassword, setDeletePassword] = useState("");

  const { register, handleSubmit, reset, formState: { errors } } = useForm<PasswordValues>({
    resolver: zodResolver(passwordSchema),
  });

  const changePassword = useMutation({
    mutationFn: (values: PasswordValues) =>
      api("/api/auth/change-password", { method: "POST", body: values }),
    onSuccess: () => {
      reset();
      toast("Password updated. Please log in again.", "success");
      tokenStore.clear();
      router.push("/auth/login");
    },
    onError: (error) =>
      toast(error instanceof ApiError ? error.message : "Password change failed.", "error"),
  });

  const deleteAccount = useMutation({
    mutationFn: () =>
      api("/api/auth/delete-account", {
        method: "POST",
        body: { email: "confirm@confirm.local", password: deletePassword },
      }),
    onSuccess: () => {
      tokenStore.clear();
      router.push("/");
    },
    onError: (error) =>
      toast(error instanceof ApiError ? error.message : "Account deletion failed.", "error"),
  });

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Settings</h1>
        <p className="text-sm text-slate-500">Security and account management.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Change password</CardTitle>
          <CardDescription>All sessions are logged out after a password change.</CardDescription>
        </CardHeader>
        <CardContent>
          <form
            onSubmit={handleSubmit((values) => changePassword.mutate(values))}
            className="space-y-4"
            noValidate
          >
            <div>
              <Label htmlFor="current_password">Current password</Label>
              <Input id="current_password" type="password" autoComplete="current-password" {...register("current_password")} />
              <FieldError message={errors.current_password?.message} />
            </div>
            <div>
              <Label htmlFor="new_password">New password</Label>
              <Input id="new_password" type="password" autoComplete="new-password" {...register("new_password")} />
              <FieldError message={errors.new_password?.message} />
            </div>
            <Button type="submit" loading={changePassword.isPending}>
              Update password
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card className="border-rose-200">
        <CardHeader>
          <CardTitle className="text-rose-700">Danger zone</CardTitle>
          <CardDescription>
            Deleting your account permanently removes your resumes, uploaded files,
            embeddings, matches, interviews and applications.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button variant="destructive" onClick={() => setDeleteOpen(true)}>
            Delete account
          </Button>
        </CardContent>
      </Card>

      <Dialog open={deleteOpen} onClose={() => setDeleteOpen(false)} title="Delete account?">
        <p className="text-sm text-slate-600">
          This action cannot be undone. All your data will be permanently deleted.
          Enter your password to confirm.
        </p>
        <div className="mt-4">
          <Label htmlFor="delete-password">Password</Label>
          <Input
            id="delete-password"
            type="password"
            value={deletePassword}
            onChange={(e) => setDeletePassword(e.target.value)}
          />
        </div>
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="outline" onClick={() => setDeleteOpen(false)}>
            Cancel
          </Button>
          <Button
            variant="destructive"
            disabled={!deletePassword}
            loading={deleteAccount.isPending}
            onClick={() => deleteAccount.mutate()}
          >
            Permanently delete
          </Button>
        </div>
      </Dialog>
    </div>
  );
}
