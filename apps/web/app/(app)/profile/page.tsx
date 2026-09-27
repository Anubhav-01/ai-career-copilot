"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { X } from "lucide-react";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { FieldError, Input, Label } from "@/components/ui/input";
import { PageSkeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { ApiError, api } from "@/lib/api";
import type { Profile } from "@/types/api";

const schema = z.object({
  headline: z.string().max(255).optional(),
  location: z.string().max(255).optional(),
  phone: z.string().max(50).optional(),
  experience_years: z.coerce.number().min(0).max(60).optional(),
  education_level: z.string().max(100).optional(),
});

type FormValues = z.infer<typeof schema>;

export default function ProfilePage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [targetRoles, setTargetRoles] = useState<string[]>([]);
  const [roleInput, setRoleInput] = useState("");

  const { data: profile, isLoading } = useQuery({
    queryKey: ["profile"],
    queryFn: () => api<Profile>("/api/profile"),
  });

  const { register, handleSubmit, reset, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
  });

  useEffect(() => {
    if (profile) {
      reset({
        headline: profile.headline ?? "",
        location: profile.location ?? "",
        phone: profile.phone ?? "",
        experience_years: profile.experience_years ?? undefined,
        education_level: profile.education_level ?? "",
      });
      setTargetRoles(profile.target_roles ?? []);
    }
  }, [profile, reset]);

  const save = useMutation({
    mutationFn: (values: FormValues) =>
      api<Profile>("/api/profile", {
        method: "PUT",
        body: { ...values, target_roles: targetRoles },
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast("Profile saved.", "success");
    },
    onError: (error) =>
      toast(error instanceof ApiError ? error.message : "Save failed.", "error"),
  });

  const addRole = () => {
    const value = roleInput.trim();
    if (value && !targetRoles.includes(value) && targetRoles.length < 5) {
      setTargetRoles([...targetRoles, value]);
    }
    setRoleInput("");
  };

  if (isLoading) return <PageSkeleton />;

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Profile</h1>
        <p className="text-sm text-slate-500">
          Your target roles and experience sharpen resume scoring and job matching.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Career profile</CardTitle>
          <CardDescription>All fields are optional but improve AI results.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit((values) => save.mutate(values))} className="space-y-4" noValidate>
            <div>
              <Label htmlFor="headline">Headline</Label>
              <Input id="headline" placeholder="e.g. Backend engineer focused on applied AI" {...register("headline")} />
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <Label htmlFor="location">Location</Label>
                <Input id="location" {...register("location")} />
              </div>
              <div>
                <Label htmlFor="phone">Phone</Label>
                <Input id="phone" {...register("phone")} />
              </div>
              <div>
                <Label htmlFor="experience_years">Years of experience</Label>
                <Input id="experience_years" type="number" min={0} max={60} {...register("experience_years")} />
                <FieldError message={errors.experience_years?.message} />
              </div>
              <div>
                <Label htmlFor="education_level">Education level</Label>
                <Input id="education_level" placeholder="e.g. B.S. Computer Science" {...register("education_level")} />
              </div>
            </div>

            <div>
              <Label htmlFor="role-input">Target roles (up to 5)</Label>
              <div className="mt-1 flex gap-2">
                <Input
                  id="role-input"
                  placeholder="e.g. AI Engineer"
                  value={roleInput}
                  onChange={(e) => setRoleInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      addRole();
                    }
                  }}
                />
                <Button type="button" variant="secondary" onClick={addRole}>
                  Add
                </Button>
              </div>
              <div className="mt-2 flex flex-wrap gap-1.5">
                {targetRoles.map((role) => (
                  <Badge key={role} className="gap-1">
                    {role}
                    <button
                      type="button"
                      aria-label={`Remove ${role}`}
                      onClick={() => setTargetRoles(targetRoles.filter((r) => r !== role))}
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </Badge>
                ))}
              </div>
            </div>

            <Button type="submit" loading={save.isPending}>
              Save profile
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
